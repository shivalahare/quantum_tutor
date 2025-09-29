from rest_framework import serializers
from .models import (
    User, QuantumCircuit, CircuitGate, Explanation,
    SimulationResult, QASession, QuizQuestion
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'difficulty_level']

class CircuitGateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CircuitGate
        fields = ['id', 'gate_type', 'qubits', 'parameters', 'step_order']

class QuantumCircuitSerializer(serializers.ModelSerializer):
    gates = CircuitGateSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = QuantumCircuit
        fields = [
            'id', 'title', 'qiskit_code', 'num_qubits', 'num_classical_bits',
            'circuit_diagram_svg', 'created_at', 'updated_at', 'gates', 'user'
        ]

class SimulationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationResult
        fields = ['id', 'statevector', 'probabilities', 'counts', 'shots', 'created_at']

class QASessionSerializer(serializers.ModelSerializer):
    circuit_title = serializers.CharField(source='circuit.title', read_only=True)
    
    class Meta:
        model = QASession
        fields = ['id', 'question', 'answer', 'circuit', 'circuit_title', 'created_at']

class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = ['id', 'question', 'options', 'correct_answer', 'explanation', 'difficulty_level']