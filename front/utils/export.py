import json
from reportlab.pdfgen import canvas



def export_as_json(input_text: str, fields: dict):
    data = {
        'raw_text': input_text,
        'fields': fields
    }

    return json.dumps(data, ensure_ascii=False, indent=4)


def export_as_txt(fields: dict):
    return '\n\n'.join(f'{field}:\n{value}' for field, value in fields.items() if value)


# def export_as_pdf(fields: dict):
#     pdf = fpdf.FPDF(format='A4')
#     pdf.add_page()
#     # pdf.cell(200, 10, txt=input_text, ln=1, align='C')
#     for field, value in fields.items():
#         if not value:
#             continue
#         pdf.set_font('Arial', '', 20)
#         pdf.cell(200, 10, txt=field, ln=1, align='C')
#         pdf.set_font('Arial', '', 16)
#         pdf.cell(200, 10, txt=value, ln=1, align='C')
#
#     # Создаем новый pdf файл
#     canvasObj = canvas.Canvas(".temp.pdf")
#
#     # Задаем шрифт и размер шрифта
#     canvasObj.setFont("Helvetica", 14)
#
#     # Записываем текст в файл
#     text = "Пример текста на русском языке"
#     canvasObj.drawString(100, 750, text)
#
#     # Сохраняем файл
#     canvasObj.save()
#     pdf.output()
#     return ''
