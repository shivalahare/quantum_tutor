from .openrouter_tutor import OpenRouterTutor
import os
from django.conf import settings

class AITutor:
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        
        if self.provider == 'openrouter':
            self.client = OpenRouterTutor()
        else:
            # Fallback to original implementation for other providers
            self.client = None
            # ... (keep original OpenAI/Anthropic code as fallback)
    
    def generate_gate_explanation(self, gate_type, difficulty_level, context_gates=None):
        """Generate explanation for a quantum gate"""
        return self.client.generate_gate_explanation(gate_type, difficulty_level, context_gates)
    
    def answer_question(self, question, circuit_context=None, user_difficulty='beginner'):
        """Answer user's quantum computing question"""
        return self.client.answer_question(question, circuit_context, user_difficulty)
    
    def generate_quiz_question(self, circuit, difficulty_level):
        """Generate a quiz question based on the circuit"""
        return self.client.generate_quiz_question(circuit, difficulty_level)