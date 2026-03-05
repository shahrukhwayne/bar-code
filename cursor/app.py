import os
import csv
import io
import zipfile

from flask import Flask, render_template, request, session, send_file, after_this_request
from barcode import get_barcode_class
from barcode.writer import ImageWriter
from openpyxl import load_workbook
from PIL import Image, ImageDraw, ImageFont


def create_app():

    app = Flask(__name__)
    app.secret_key = os.urandom(24)

    os.makedirs("static/barcodes", exist_ok=True)

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


# ---------------- TEXT WRAP ----------------

    def split_text_into_lines(text, max_chars=45):

        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:

            if len(current_line) + len(word) + 1 > max_chars:
                lines.append(current_line)
                current_line = word

            else:

                if current_line:
                    current_line += " "

                current_line += word

        if current_line:
            lines.append(current_line)

        return lines


# ---------------- BARCODE IMAGE ----------------

    def generate_barcode_image(sku, title):

        barcode_class = get_barcode_class("code128")

        barcode_options = {
            "module_width": 0.9,
            "module_height": 30,
            "font_size": 0,
            "quiet_zone": 8,
            "dpi": 200
        }

        barcode_obj = barcode_class(sku, writer=ImageWriter())

        buffer = io.BytesIO()
        barcode_obj.write(buffer, options=barcode_options)
        buffer.seek(0)

        barcode_img = Image.open(buffer).convert("RGB")

        padding = 40

        try:
            sku_font = ImageFont.truetype("font/DejaVuSans-Bold.ttf", 30)
            title_font = ImageFont.truetype("font/DejaVuSans-Bold.ttf", 20)
        except:
            sku_font = ImageFont.load_default()
            title_font = ImageFont.load_default()

        lines = split_text_into_lines(title, 45)

        line_height = title_font.getbbox("A")[3]
        title_height = (line_height + 10) * len(lines)

        new_height = barcode_img.height + padding + 60 + title_height + 40

        new_img = Image.new("RGB", (barcode_img.width, new_height), (255, 255, 255))

        new_img.paste(barcode_img, (0, padding))

        draw = ImageDraw.Draw(new_img)

        sku_bbox = sku_font.getbbox(sku)
        sku_width = sku_bbox[2] - sku_bbox[0]

        sku_x = (new_img.width - sku_width) / 2
        sku_y = barcode_img.height + padding + 5

        draw.text((sku_x, sku_y), sku, font=sku_font, fill="black")

        text_y = sku_y + 55

        for line in lines:

            bbox = title_font.getbbox(line)
            text_width = bbox[2] - bbox[0]

            text_x = (new_img.width - text_width) / 2

            draw.text((text_x, text_y), line, font=title_font, fill="black")

            text_y += (bbox[3] - bbox[1]) + 10

        final_buffer = io.BytesIO()
        new_img.save(final_buffer, format="PNG")
        final_buffer.seek(0)

        return final_buffer


# ---------------- HOME ----------------

    @app.route("/")
    def index():

        return render_template("index.html", barcode_items=None)


# ---------------- GENERATE ----------------

    @app.route("/generate-barcodes", methods=["POST"])
    def generate_barcodes():

        # delete old preview if exists
        preview_path = "static/barcodes/preview.png"

        if os.path.exists(preview_path):
            os.remove(preview_path)

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

        session["barcode_rows"] = rows

        results = []

        if rows:

            sku, title = rows[0]

            img_buffer = generate_barcode_image(sku, title)

            with open(preview_path, "wb") as f:
                f.write(img_buffer.getbuffer())

            results.append({
                "url": "/static/barcodes/preview.png",
                "value": sku,
                "title": title
            })

        return render_template("index.html", barcode_items=results)


# ---------------- DOWNLOAD ----------------

    @app.route("/download-barcodes")
    def download_barcodes():

        rows = session.get("barcode_rows")

        if not rows:
            return render_template("index.html", barcode_error="Generate first")

        zip_buffer = io.BytesIO()

        BATCH_SIZE = 200

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:

            for i in range(0, len(rows), BATCH_SIZE):

                batch = rows[i:i+BATCH_SIZE]

                for sku, title in batch:

                    img_buffer = generate_barcode_image(sku, title)

                    img = Image.open(img_buffer).convert("RGB")

                    pdf_buffer = io.BytesIO()

                    img.save(pdf_buffer, "PDF", resolution=150.0)

                    pdf_buffer.seek(0)

                    zip_file.writestr(f"{sku}.pdf", pdf_buffer.read())

        zip_buffer.seek(0)

        preview_path = "static/barcodes/preview.png"

        @after_this_request
        def cleanup(response):

            try:
                if os.path.exists(preview_path):
                    os.remove(preview_path)
            except Exception:
                pass

            return response

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