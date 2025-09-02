# students/management/commands/seed_school.py
from django.core.management.base import BaseCommand
from exams.models import ClassLevel
from students.models import ClassSection

class Command(BaseCommand):
    help = "Seed ClassLevel (1-12 x English/Tamil) and ClassSection (A-D per level)"

    def add_arguments(self, parser):
        parser.add_argument('--mediums', nargs='*', default=['English', 'Tamil'],
                            help="List of mediums to create (default: English Tamil)")

    def handle(self, *args, **opts):
        mediums = opts['mediums']
        classes = [str(i) for i in range(1, 13)]
        sections = list("ABCD")

        created_levels = 0
        created_sections = 0

        # 1) Create/find ClassLevel
        for c in classes:
            for m in mediums:
                level, lvl_created = ClassLevel.objects.get_or_create(name=c, medium=m)
                created_levels += int(lvl_created)

                # 2) Create/find ClassSection under that level
                for s in sections:
                    _, sec_created = ClassSection.objects.get_or_create(
                        class_level=level,  # FK to exams.ClassLevel
                        class_name=c,
                        section=s,
                    )
                    created_sections += int(sec_created)

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {created_levels} ClassLevel(s), {created_sections} ClassSection(s)."
        ))
