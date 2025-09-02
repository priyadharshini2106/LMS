# students/management/commands/seed_classsections.py
from django.core.management.base import BaseCommand
from students.models import ClassSection

class Command(BaseCommand):
    help = "Seed ClassSection with classes 1-12 and sections A-D"

    def handle(self, *args, **options):
        classes = [str(i) for i in range(1, 13)]
        sections = list("ABCD")
        created = 0
        for c in classes:
            for s in sections:
                _, was_created = ClassSection.objects.get_or_create(class_name=c, section=s)
                created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Done. Created {created} new rows."))
