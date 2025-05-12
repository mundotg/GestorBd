import pdfkit

path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

pdfkit.from_file(r'c:\Users\IT\Documents\portifolio\cv-francemy-pdf.html', 'saida.pdf', configuration=config)
