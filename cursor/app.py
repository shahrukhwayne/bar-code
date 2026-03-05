import os
import csv
import io
import zipfile
from datetime import datetime, timedelta

from flask import Flask, render_template, request, session, send_file
from barcode import get_barcode_class
from barcode.writer import ImageWriter
from openpyxl import load_workbook
from PIL import Image, ImageDraw, ImageFont


def create_app():

    app = Flask(__name__)
    app.secret_key = os.urandom(24)

    app.config["BARCODE_FOLDER"] = os.path.join(app.root_path, "static", "barcodes")

    os.makedirs(app.config["BARCODE_FOLDER"], exist_ok=True)

    # ---------------- CLEANUP ----------------
    def cleanup_old_pngs(folder):

        cutoff = datetime.now() - timedelta(minutes=30)

        for name in os.listdir(folder):

            if name.endswith(".png"):

                path = os.path.join(folder, name)

                if datetime.fromtimestamp(os.path.getmtime(path)) < cutoff:
                    os.remove(path)

    # ---------------- READ CSV ----------------
    def read_csv(file_bytes):

        text = file_bytes.decode("utf-8-sig", errors="replace")

        stream = io.StringIO(text)

        reader = csv.reader(stream)

        next(reader, None)

        rows = []

        for row in reader:

            if not row or len(row) < 2:
                continue

            sku = row[0].strip()
            title = row[1].strip() if row[1] else ""

            if not sku or sku.lower() == "none":
                continue

            rows.append((sku, title))

        return rows

    # ---------------- READ XLSX ----------------
    def read_xlsx(file_bytes):

        wb = load_workbook(filename=io.BytesIO(file_bytes), read_only=True)

        ws = wb.active

        rows = []

        for i, row in enumerate(ws.iter_rows(values_only=True)):

            if i == 0:
                continue

            if not row or len(row) < 2:
                continue

            sku = row[0]
            title = row[1]

            if not sku:
                continue

            sku = str(sku).strip()

            if not sku or sku.lower() == "none":
                continue

            title = "" if title is None else str(title).strip()

            rows.append((sku, title))

        return rows

    # ---------------- TEXT LINE BREAK ----------------
    def split_text_into_lines(text, max_length=60):

        words = text.split(" ")

        lines = []

        current_line = ""

        for word in words:

            if len(current_line) + len(word) + 1 > max_length:

                lines.append(current_line)

                current_line = word

            else:

                if current_line:
                    current_line += " "

                current_line += word

        if current_line:
            lines.append(current_line)

        return lines

    # ---------------- GENERATE BARCODE ----------------
    def generate_barcode_image(sku, title):

        barcode_class = get_barcode_class("code128")

        barcode_options = {
            "module_width": 0.7,
            "module_height": 35,
            "font_size": 0,
            "quiet_zone": 12,
            "dpi": 600
        }

        barcode_path = os.path.join(app.config["BARCODE_FOLDER"], f"barcode_{sku}")

        barcode_obj = barcode_class(sku, writer=ImageWriter())

        barcode_obj.save(barcode_path, options=barcode_options)

        barcode_img = Image.open(barcode_path + ".png")

        new_height = barcode_img.height + 200

        new_img = Image.new(
            "RGB",
            (barcode_img.width, new_height),
            (255, 255, 255)
        )

        new_img.paste(barcode_img, (0, 10))

        draw = ImageDraw.Draw(new_img)

        # SKU FONT
        try:
            sku_font = ImageFont.truetype("arial.ttf", 55)
        except:
            sku_font = ImageFont.load_default()

        sku_bbox = sku_font.getbbox(sku)

        sku_width = sku_bbox[2] - sku_bbox[0]

        sku_x = (new_img.width - sku_width) / 2

        sku_y = barcode_img.height + 10

        draw.text((sku_x, sku_y), sku, font=sku_font, fill="black")

        # TITLE FONT
        try:
            title_font = ImageFont.truetype("arial.ttf", 40)
        except:
            title_font = ImageFont.load_default()

        lines = split_text_into_lines(title, 60)

        text_y = sku_y + 70

        for line in lines:

            bbox = title_font.getbbox(line)

            text_width = bbox[2] - bbox[0]

            text_x = (new_img.width - text_width) / 2

            draw.text((text_x, text_y), line, font=title_font, fill="black")

            text_y += (bbox[3] - bbox[1]) + 15

        final_path = os.path.join(app.config["BARCODE_FOLDER"], f"{sku}.png")

        new_img.save(final_path)

        return final_path

    # ---------------- HOME ----------------
    @app.route("/")
    def index():

        return render_template("index.html", barcode_items=None)

    # ---------------- GENERATE ----------------
    @app.route("/generate-barcodes", methods=["POST"])
    def generate_barcodes():

        cleanup_old_pngs(app.config["BARCODE_FOLDER"])

        uploaded = request.files.get("file")

        if not uploaded:
            return render_template("index.html", barcode_error="Upload file required")

        file_bytes = uploaded.read()

        if uploaded.filename.endswith(".csv"):
            rows = read_csv(file_bytes)

        elif uploaded.filename.endswith(".xlsx"):
            rows = read_xlsx(file_bytes)

        else:
            return render_template("index.html", barcode_error="Only CSV/XLSX allowed")

        results = []

        for sku, title in rows:

            generate_barcode_image(sku, title)

            results.append({
                "url": "/static/barcodes/" + f"{sku}.png",
                "value": sku,
                "title": title
            })

        session["barcodes"] = results

        return render_template("index.html", barcode_items=results)

    # ---------------- DOWNLOAD ----------------
    @app.route("/download-barcodes")
    def download_barcodes():

        items = session.get("barcodes")

        if not items:
            return render_template("index.html", barcode_error="Generate first")

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:

            for item in items:

                img_path = os.path.join(app.config["BARCODE_FOLDER"], f"{item['value']}.png")

                img = Image.open(img_path).convert("RGB")

                pdf_buffer = io.BytesIO()

                img.save(pdf_buffer, "PDF", resolution=300.0)

                pdf_buffer.seek(0)

                zip_file.writestr(f"{item['value']}.pdf", pdf_buffer.read())

        zip_buffer.seek(0)

        # delete images after download
        for item in items:

            img_path = os.path.join(app.config["BARCODE_FOLDER"], f"{item['value']}.png")

            if os.path.exists(img_path):
                os.remove(img_path)

        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name="barcodes.zip"
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)