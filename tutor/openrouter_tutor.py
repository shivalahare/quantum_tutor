import requests
import json
import os
from django.conf import settings

class OpenRouterTutor:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = settings.OPENROUTER_MODEL
        self.is_configured = bool(self.api_key)
    
    def generate_gate_explanation(self, gate_type, difficulty_level, context_gates=None):
        """Generate explanation for a quantum gate using OpenRouter"""
        prompt = self._build_gate_explanation_prompt(gate_type, difficulty_level, context_gates)
        return self._call_openrouter(prompt)
    
    def answer_question(self, question, circuit_context=None, user_difficulty='beginner'):
        """Answer user's quantum computing question using OpenRouter"""
        prompt = self._build_qa_prompt(question, circuit_context, user_difficulty)
        return self._call_openrouter(prompt, max_tokens=1000)
    
    def generate_quiz_question(self, circuit, difficulty_level):
        """Generate a quiz question based on the circuit using OpenRouter"""
        prompt = self._build_quiz_prompt(circuit, difficulty_level)
        response = self._call_openrouter(prompt, max_tokens=800)
        return self._parse_quiz_response(response)
    
    def _build_gate_explanation_prompt(self, gate_type, difficulty_level, context_gates):
        base_prompts = {
            'beginner': f"""
            Explain the {gate_type} quantum gate to a complete beginner who has no background in quantum computing.
            Use simple analogies from everyday life.
            Focus on what the gate does in simple terms, not the mathematics.
            Include 2-3 practical analogies.
            Keep it under 200 words.
            """,
            
            'intermediate': f"""
            Explain the {gate_type} quantum gate to someone with basic quantum computing knowledge.
            Include the mathematical representation and matrix form if applicable.
            Explain how it affects qubit states.
            Mention common use cases in quantum algorithms.
            Keep it under 300 words.
            """,
            
            'advanced': f"""
            Provide a comprehensive technical explanation of the {gate_type} quantum gate.
            Include:
            - Mathematical representation and matrix
            - Effect on Bloch sphere
            - Quantum mechanical principles involved
            - Role in quantum algorithms
            - Experimental implementations
            Keep it under 400 words.
            """,
            
            'eli5': f"""
            Explain the {gate_type} quantum gate like I'm 5 years old.
            Use the simplest possible language and fun analogies.
            Make it engaging and easy to understand.
            Avoid any technical terms.
            Keep it under 150 words.
            """
        }
        
        prompt = base_prompts.get(difficulty_level, base_prompts['beginner'])
        
        if context_gates:
            context_str = ", ".join(context_gates)
            prompt += f"\n\nContext: This gate is used after {context_str} gates in the circuit."
        
        return prompt
    
    def _build_qa_prompt(self, question, circuit_context, user_difficulty):
        prompt = f"""
        You are an expert quantum computing tutor. Answer the following question from a {user_difficulty} level student.
        
        Question: {question}
        """
        
        if circuit_context:
            prompt += f"""
            
            Circuit Context:
            - Number of qubits: {circuit_context.get('num_qubits', 'N/A')}
            - Gates used: {', '.join(circuit_context.get('gates', []))}
            - Circuit purpose: {circuit_context.get('purpose', 'General quantum circuit')}
            """
        
        prompt += """
        
        Please provide:
        1. A clear, direct answer appropriate for the student's level
        2. A simple analogy or example if applicable
        3. Key takeaways
        4. Suggestions for further learning if relevant
        
        Keep the explanation engaging and educational.
        """
        
        return prompt
    
    def _build_quiz_prompt(self, circuit, difficulty_level):
        gates_used = [gate.gate_type for gate in circuit.gates.all()]
        
        prompt = f"""
        Generate a multiple-choice quiz question about this quantum circuit:
        - Title: {circuit.title}
        - Number of qubits: {circuit.num_qubits}
        - Gates used: {', '.join(gates_used)}
        - Difficulty level: {difficulty_level}
        
        Please provide:
        1. A clear question about the circuit's behavior or properties
        2. Four answer options (A, B, C, D)
        3. The correct answer (0-3 index)
        4. A brief explanation of why it's correct
        
        Format your response as:
        QUESTION: [question text]
        OPTIONS: [option A] | [option B] | [option C] | [option D]
        CORRECT: [index 0-3]
        EXPLANATION: [explanation text]
        """
        
        return prompt
    
    def _call_openrouter(self, prompt, max_tokens=500):
        if not self.is_configured:
            return self._fallback_response(prompt)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://quantum-tutor.com",  # Required by OpenRouter
                "X-Title": "Quantum Tutor"  # Required by OpenRouter
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                error_msg = f"OpenRouter API error {response.status_code}: {response.text}"
                return self._fallback_response(prompt, error_msg)
                
        except Exception as e:
            error_msg = f"OpenRouter connection error: {str(e)}"
            return self._fallback_response(prompt, error_msg)
    
    def _parse_quiz_response(self, response):
        # Simple parsing of the quiz response
        lines = response.split('\n')
        quiz_data = {
            'question': '',
            'options': [],
            'correct_answer': 0,
            'explanation': ''
        }
        
        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith('QUESTION:'):
                current_section = 'question'
                quiz_data['question'] = line.replace('QUESTION:', '').strip()
            elif line.startswith('OPTIONS:'):
                current_section = 'options'
                options_text = line.replace('OPTIONS:', '').strip()
                quiz_data['options'] = [opt.strip() for opt in options_text.split('|')]
            elif line.startswith('CORRECT:'):
                current_section = 'correct'
                correct_text = line.replace('CORRECT:', '').strip()
                try:
                    quiz_data['correct_answer'] = int(correct_text)
                except ValueError:
                    quiz_data['correct_answer'] = 0
            elif line.startswith('EXPLANATION:'):
                current_section = 'explanation'
                quiz_data['explanation'] = line.replace('EXPLANATION:', '').strip()
            elif current_section == 'explanation' and line:
                quiz_data['explanation'] += ' ' + line
        
        # Ensure we have at least 4 options
        while len(quiz_data['options']) < 4:
            quiz_data['options'].append(f"Option {len(quiz_data['options']) + 1}")
        
        return quiz_data
    
    def _fallback_response(self, prompt, error_msg=None):
        """Provide fallback responses when OpenRouter is unavailable"""
        if "gate" in prompt.lower():
            if "h gate" in prompt.lower() or "hadamard" in prompt.lower():
                return "The Hadamard gate (H gate) creates superposition. It turns a |0⟩ state into (|0⟩ + |1⟩)/√2 and a |1⟩ state into (|0⟩ - |1⟩)/√2. This puts the qubit in an equal probability state of being 0 or 1 when measured."
            elif "x gate" in prompt.lower():
                return "The X gate is the quantum equivalent of a classical NOT gate. It flips |0⟩ to |1⟩ and |1⟩ to |0⟩. Think of it like flipping a bit from 0 to 1 or vice versa."
            elif "cnot" in prompt.lower() or "cx gate" in prompt.lower():
                return "The CNOT gate (controlled-NOT) is a two-qubit gate that flips the second qubit only if the first qubit is |1⟩. It's essential for creating quantum entanglement."
        
        if error_msg:
            return f"AI service temporarily unavailable. {error_msg}\n\nPlease check your OpenRouter API key configuration."
        else:
            return "AI tutor is currently unavailable. Please check your OpenRouter API key configuration in the environment variables."