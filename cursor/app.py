import os
import uuid
import csv
import io
import zipfile
from datetime import datetime, timedelta
from textwrap import wrap

from flask import Flask, render_template, request, url_for, session, send_file
from barcode import get_barcode_class
from barcode.writer import ImageWriter
from openpyxl import load_workbook


def create_app():
    app = Flask(__name__)
    app.secret_key = "change-me-in-production"

    app.config["BARCODE_FOLDER"] = os.path.join(app.root_path, "static", "barcodes")
    app.config["MAX_BULK_ROWS"] = 50

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

    # ---------------- GENERATE BARCODE IMAGE ----------------
    def generate_barcode(sku, title):
        Barcode = get_barcode_class("code128")
        filename_base = uuid.uuid4().hex
        out_base = os.path.join(app.config["BARCODE_FOLDER"], filename_base)

        barcode_obj = Barcode(sku, writer=ImageWriter())
        saved_path = barcode_obj.save(
            out_base,
            options={
                "write_text": False,
                "module_width": 0.35,
                "module_height": 14.0,
                "quiet_zone": 2.0,
                "dpi": 300,
            },
        )

        saved_name = os.path.basename(saved_path)

        return {
            "url": url_for("static", filename=f"barcodes/{saved_name}"),
            "filename": saved_name,
            "value": sku,
            "title": title,
        }

    # ---------------- HOME ----------------
    @app.get("/")
    def index():
        return render_template("index.html", barcode_items=None, barcode_error=None)

    # ---------------- GENERATE ----------------
    @app.post("/generate-barcodes")
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

        rows = rows[: app.config["MAX_BULK_ROWS"]]

        barcode_items = []
        for sku, title in rows:
            barcode_items.append(generate_barcode(sku, title))

        session["last_barcodes"] = barcode_items

        return render_template("index.html", barcode_items=barcode_items, barcode_error=None)

    # ---------------- DOWNLOAD ZIP (SEPARATE PDF FILES) ----------------
    @app.get("/download-barcodes")
    def download_barcodes():
        items = session.get("last_barcodes")
        if not items:
            return render_template("index.html", barcode_error="Generate first")

        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for item in items:

                pdf_buffer = io.BytesIO()
                pdf = canvas.Canvas(pdf_buffer, pagesize=A4)
                page_width, page_height = A4

                img_path = os.path.join(app.config["BARCODE_FOLDER"], item["filename"])

                img_width = page_width - 100
                img_height = 150

                x = (page_width - img_width) / 2
                y = (page_height - img_height) / 2

                pdf.drawImage(img_path, x, y, width=img_width, height=img_height)

                # SKU
                pdf.setFont("Helvetica-Bold", 14)
                pdf.drawCentredString(page_width / 2, y - 30, item["value"])

                # TITLE WRAP
                pdf.setFont("Helvetica", 11)
                wrapped_lines = wrap(item["title"], width=60)

                text_y = y - 50
                for line in wrapped_lines:
                    pdf.drawCentredString(page_width / 2, text_y, line)
                    text_y -= 15

                pdf.save()
                pdf_buffer.seek(0)

                # Save as SKU.pdf inside ZIP
                filename = f"{item['value']}.pdf"
                zip_file.writestr(filename, pdf_buffer.read())

        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name="barcodes.zip",
        )

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)