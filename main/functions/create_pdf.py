from fpdf import FPDF
import re


def remove_non_ascii(text):
    return re.sub(r'[^\x00-\x7F]', '', text)


def create_pdf_function(summaries, headings, output_file):
    class PDF(FPDF):
        def header(self):
            self.image('src/background.jpg', 0, 0, 210, 297)

    pdf = PDF()
    pdf.add_page()
    for i in range(len(summaries)):
        # Remove non-ASCII characters from headings and summaries
        cleaned_heading = remove_non_ascii(headings[i])
        cleaned_summary = remove_non_ascii(summaries[i])

        pdf.set_font("Times", 'B', size=16)
        # Decreased cell width to 180
        pdf.cell(180, 10, txt=cleaned_heading, ln=1, align="C")
        pdf.set_font("Arial", size=10)
        # Decreased cell width to 180
        pdf.multi_cell(180, 10, txt=cleaned_summary)
    pdf.output(output_file)
