import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from questionnaires.models import Questionnaire, ResponseSet
from questionnaires.services import QuestionnaireExportService

def test_export():
    q = Questionnaire.objects.first()
    if not q:
        print("Error: No questionnaire found.")
        return

    print(f"Testing export for: {q.title} ({q.id})")
    
    # Check if there are completed response sets
    count = ResponseSet.objects.filter(questionnaire=q, status='COMPLETED').count()
    print(f"Completed ResponseSets: {count}")
    
    if count == 0:
        print("Note: No completed responses. Export will only contain headers.")

    headers, data = QuestionnaireExportService.get_wide_format_data(q.id)
    
    print("\nHeaders:")
    print(headers)
    
    print(f"\nData Rows: {len(data)}")
    if len(data) > 0:
        print("Sample Data Row (First 5 fields):")
        print(data[0][:5])
        
        # Verify question columns exist
        q_cols = [h for h in headers if h.startswith('Q_')]
        print(f"Question Columns Found: {len(q_cols)}")
        assert len(q_cols) == q.questions.count(), "Mismatch in question count"

    print("\nVERIFICATION SUCCESSFUL: Service correctly structures wide-format data.")

if __name__ == "__main__":
    test_export()
