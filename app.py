from flask import Flask, render_template, request, redirect, send_file
import sqlite3
from datetime import datetime, timedelta
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.graphics.barcode import eanbc
from reportlab.graphics.shapes import Drawing
from reportlab.lib.units import mm
import io
import webbrowser

app = Flask(__name__)
DB = "database.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            designation TEXT,
            ean TEXT,
            dlc_days INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    return render_template("index.html", products=products)

@app.route("/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        designation = request.form["designation"]
        ean = request.form["ean"]
        dlc_days = request.form["dlc_days"]

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO products (designation, ean, dlc_days) VALUES (?, ?, ?)",
                  (designation, ean, dlc_days))
        conn.commit()
        conn.close()
        return redirect("/")

    return render_template("create_product.html")

@app.route("/generate/<int:product_id>", methods=["POST"])
def generate(product_id):

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    conn.close()

    designation = product[1]
    ean = product[2]
    dlc_days = int(product[3])

    poids = request.form["poids"]
    operateur = request.form["operateur"]

    today = datetime.today()
    dlc = today + timedelta(days=dlc_days)

    lot = designation[:3].upper() + today.strftime("%d%m%y%H%M")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(60*mm, 40*mm))
    elements = []
    styles = getSampleStyleSheet()
    normal = styles["Normal"]

    elements.append(Paragraph(f"<b>{designation}</b>", normal))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(f"Poids net : {poids} kg", normal))
    elements.append(Paragraph(f"Fabriqué le : {today.strftime('%d/%m/%Y')}", normal))
    elements.append(Paragraph(f"DLC : {dlc.strftime('%d/%m/%Y')}", normal))
    elements.append(Paragraph(f"Opérateur : {operateur}", normal))
    elements.append(Paragraph(f"Lot : {lot}", normal))
    elements.append(Spacer(1, 6))

    barcode = eanbc.Ean13BarcodeWidget(ean)
    barcode.barHeight = 15 * mm
    barcode.barWidth = 0.4

    drawing = Drawing(200, 50)
    drawing.add(barcode)
    elements.append(drawing)

    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="etiquette.pdf")

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True)
