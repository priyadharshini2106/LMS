from django.template.loader import render_to_string
from weasyprint import HTML
from django.http import HttpResponse

def generate_timetable_pdf(request, context, filename="timetable.pdf"):
    html_string = render_to_string('timetable/timetable_pdf.html', context)
    html = HTML(string=html_string)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    html.write_pdf(target=response)
    return response
