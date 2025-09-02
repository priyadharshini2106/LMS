from timetable.models import ClassLevel, Period, Subject, Teacher, TimetableSlot
from django.db import transaction

def auto_generate_timetable():
    try:
        with transaction.atomic():
            for class_level in ClassLevel.objects.all():
                subjects = Subject.objects.filter(class_level=class_level)
                periods = Period.objects.all()
                teachers = Teacher.objects.filter(subjects__in=subjects).distinct()

                # Skip if already generated
                if TimetableSlot.objects.filter(class_level=class_level).exists():
                    continue

                subject_list = list(subjects)
                teacher_list = list(teachers)

                subj_idx = 0
                teach_idx = 0

                for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
                    for period in periods:
                        if not subject_list or not teacher_list:
                            continue

                        # Loop around
                        subject = subject_list[subj_idx % len(subject_list)]
                        teacher = teacher_list[teach_idx % len(teacher_list)]

                        TimetableSlot.objects.create(
                            class_level=class_level,
                            day=day,
                            period=period,
                            subject=subject,
                            teacher=teacher
                        )

                        subj_idx += 1
                        teach_idx += 1
    except Exception as e:
        print(f"[❌] Auto generation failed: {e}")
