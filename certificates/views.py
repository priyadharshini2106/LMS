from django.shortcuts import render
from django.http import HttpResponse
from students.models import Student
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
import os

# ✅ Transfer Certificate Generator with Graceful Error Handling
def generate_transfer_certificate(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        context = {
            'error': "No student found with this ID. Please update the student list in the Student module."
        }
        return render(request, 'certificates/student_not_found.html', context)

    html_string = render_to_string('certificates/transfer_certificate.html', {
        'student': student,
        'school_name': 'Periyanachi Hr. Sec. School',
        'school_address': 'Karur, Tamil Nadu - 639001',
        'headmaster_name': 'Mr. Arulmani R.',
    })

    with tempfile.NamedTemporaryFile(delete=True, suffix='.pdf') as output:
        HTML(string=html_string).write_pdf(target=output.name)
        output.seek(0)
        response = HttpResponse(output.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename=TC_{student.name.replace(" ", "_")}.pdf'
        return response


# ✅ Bonafide Certificate Generator with Graceful Error Handling
def generate_bonafide_certificate(request, student_id):
    try:
        student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        context = {
            'error': "No student found with this ID. Please update the student list in the Student module."
        }
        return render(request, 'certificates/student_not_found.html', context)

    html_string = render_to_string('certificates/bonafide_certificate.html', {
        'student': student,
        'school_name': 'Periyanachi Hr. Sec. School',
        'school_address': 'Karur, Tamil Nadu - 639001',
        'headmaster_name': 'Mr. Arulmani R.',
    })

    temp_dir = tempfile.mkdtemp(dir="D:/periyanachi_school_erp_final")
    os.environ["TMPDIR"] = temp_dir

    output_pdf_path = os.path.join(temp_dir, f"bonafide_certificate_{student_id}.pdf")
    HTML(string=html_string).write_pdf(output_pdf_path)

    with open(output_pdf_path, 'rb') as pdf_file:
        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename=Bonafide_{student.name.replace(" ", "_")}.pdf'
        return response
