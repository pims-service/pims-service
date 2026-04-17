from django.core.management.base import BaseCommand
from questionnaires.models import Questionnaire, ResponseSet
from questionnaires.services import QuestionnaireExportService

class Command(BaseCommand):
    help = 'Verifies Issue #70: Questionnaire Analytics & wide-format Export'

    def handle(self, *args, **options):
        q = Questionnaire.objects.first()
        if not q:
            self.stdout.write(self.style.ERROR("Error: No questionnaire found. Run seed_questionnaires first."))
            return

        self.stdout.write(f"Testing export for: {q.title} ({q.id})")
        
        # Check if there are completed response sets
        count = ResponseSet.objects.filter(questionnaire=q, status='COMPLETED').count()
        self.stdout.write(f"Completed ResponseSets: {count}")

        headers, data = QuestionnaireExportService.get_wide_format_data(q.id)
        
        self.stdout.write("\nHeaders:")
        self.stdout.write(str(headers))
        
        self.stdout.write(f"\nData Rows: {len(data)}")
        if len(data) > 0:
            self.stdout.write("Sample Data Row (First 5 fields):")
            self.stdout.write(str(data[0][:5]))
            
            # Verify question columns exist
            q_cols = [h for h in headers if h.startswith('Q_')]
            self.stdout.write(f"Question Columns Found: {len(q_cols)}")
            
            if len(q_cols) != q.questions.count():
                raise Exception(f"Mismatch in question count: Found {len(q_cols)}, Expected {q.questions.count()}")

        self.stdout.write(self.style.SUCCESS("\nVERIFICATION SUCCESSFUL: Service correctly structures wide-format data."))
