import os
import django
from dotenv import load_dotenv

load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tutor.openrouter_tutor import OpenRouterTutor

def test_openrouter():
    tutor = OpenRouterTutor()
    print("OpenRouter configured:", tutor.is_configured)
    
    if tutor.is_configured:
        # Test a simple question
        response = tutor.answer_question("What is a qubit?")
        print("Response:", response)
    else:
        print("Please set OPENROUTER_API_KEY in your .env file")

if __name__ == "__main__":
    test_openrouter()