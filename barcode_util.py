import os
import datetime
from barcode import EAN13
from barcode.writer import SVGWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF


# Регистрируем шрифты (указывай свои пути, если другие)
pdfmetrics.registerFont(TTFont("Roboto", "fonts/Roboto.ttf"))
pdfmetrics.registerFont(TTFont("Roboto-Bold", "fonts/Roboto-Bold.ttf"))


def generate_weight_barcode_svg(plu_code: str, weight_kg: float) -> tuple[str, str]:
    """
    Генерация весового штрихкода EAN-13 в SVG.
    """
    plu = str(plu_code).zfill(5)
    grams = int(weight_kg * 1000)
    weight = str(grams).zfill(5)
    raw = f"20{plu}{weight}"

    barcode = EAN13(raw, writer=SVGWriter())
    filename = "ean13"
    options = {
        "write_text": False,
        "module_width": 0.25,
        "module_height": 12.0  # уменьшенная высота
    }
    full_path = barcode.save(filename, options=options)
    return full_path, barcode.get_fullcode()


def generate_label(product_name: str, price_per_kg: float, weight_kg: float, plu_code: str,
                   date_str=None, output="label.pdf"):
    if date_str is None:
        date_str = datetime.datetime.now().strftime("%d.%m.%Y")

    total_price = round(price_per_kg * weight_kg, 2)
    barcode_svg_path, barcode_text = generate_weight_barcode_svg(plu_code, weight_kg)

    width_mm, height_mm = 58, 40
    c = canvas.Canvas(output, pagesize=(width_mm * mm, height_mm * mm))

    # --- Дата ---
    c.setFont("Roboto-Bold", 7)
    c.drawRightString(56 * mm, 36 * mm, date_str)

    # --- Название товара ---
    c.setFont("Roboto-Bold", 10)
    lines = product_name.split("\n")
    y = 32 * mm
    for line in lines:
        c.drawString(4 * mm, y, line.strip())
        y -= 4.2 * mm

    # --- Вес, цена за кг, PLU ---
    c.setFont("Roboto", 8)
    c.drawString(4 * mm, y, f"Вес: {int(weight_kg * 1000)} г")
    y -= 3.8 * mm
    c.drawString(4 * mm, y, f"Цена за кг: {price_per_kg:.2f} руб.")
    y -= 3.8 * mm
    c.drawString(4 * mm, y, f"PLU: {plu_code}")
    y -= 3.8 * mm

    # --- Итоговая цена ---
    c.setFont("Roboto-Bold", 14)
    c.drawCentredString(width_mm * mm / 2, 11.5 * mm, f"{total_price:.2f} руб.")

    # --- Штрихкод (SVG) ---
    drawing = svg2rlg(barcode_svg_path)
    renderPDF.draw(drawing, c, 9 * mm, 4 * mm)

    # --- Цифры под штрихкодом ---
    c.setFont("Roboto", 8)
    c.drawCentredString(width_mm * mm / 2, 2.2 * mm, barcode_text)

    # --- Обводка по краю ---
    c.setLineWidth(0.5)
    c.rect(1 * mm, 1 * mm, (width_mm - 2) * mm, (height_mm - 2) * mm)

    c.save()
    os.remove(barcode_svg_path)
    print(f"✅ Этикетка сохранена в {output}")


# 🔧 Пример использования
if __name__ == "__main__":
    generate_label(
        product_name="Филе куриное охлаждённое",
        price_per_kg=359.99,
        weight_kg=0.812,
        plu_code="10123",
        date_str="02.06.2025"
    )
