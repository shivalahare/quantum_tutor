from django.contrib.auth.models import AbstractUser
from django.db import models
import json

class User(AbstractUser):
    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_LEVELS,
        default='beginner'
    )
    
    def __str__(self):
        return f"{self.username} ({self.difficulty_level})"

class QuantumCircuit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='circuits')
    title = models.CharField(max_length=200)
    qiskit_code = models.TextField()
    num_qubits = models.IntegerField(default=1)
    num_classical_bits = models.IntegerField(default=1)
    circuit_diagram_svg = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.num_qubits} qubits)"

class CircuitGate(models.Model):
    GATE_TYPES = [
        ('h', 'Hadamard'),
        ('x', 'Pauli-X'),
        ('y', 'Pauli-Y'),
        ('z', 'Pauli-Z'),
        ('cx', 'CNOT'),
        ('rx', 'Rotation-X'),
        ('ry', 'Rotation-Y'),
        ('rz', 'Rotation-Z'),
        ('s', 'S Gate'),
        ('sdg', 'S† Gate'),
        ('t', 'T Gate'),
        ('tdg', 'T† Gate'),
        ('measure', 'Measurement'),
        ('swap', 'SWAP'),
        ('ccx', 'Toffoli'),
        ('u3', 'U3 Gate'),
    ]
    
    circuit = models.ForeignKey(QuantumCircuit, on_delete=models.CASCADE, related_name='gates')
    gate_type = models.CharField(max_length=10, choices=GATE_TYPES)
    qubits = models.JSONField()  # List of qubit indices
    parameters = models.JSONField(default=dict, blank=True)  # For parameterized gates
    step_order = models.IntegerField()  # Order in the circuit
    
    class Meta:
        ordering = ['step_order']
    
    def __str__(self):
        params = f"({self.parameters})" if self.parameters else ""
        return f"{self.gate_type}{params} on {self.qubits}"

class Explanation(models.Model):
    DIFFICULTY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('eli5', 'Explain Like I\'m 5'),
    ]
    
    gate_type = models.CharField(max_length=10, choices=CircuitGate.GATE_TYPES)
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS)
    explanation_text = models.TextField()
    analogies = models.JSONField(default=list, blank=True)  # List of analogies
    mathematical_representation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['gate_type', 'difficulty_level']
    
    def __str__(self):
        return f"{self.gate_type} - {self.difficulty_level}"

class SimulationResult(models.Model):
    circuit = models.OneToOneField(QuantumCircuit, on_delete=models.CASCADE, related_name='simulation')
    statevector = models.JSONField()  # Complex numbers as [real, imag] pairs
    probabilities = models.JSONField()  # Measurement probabilities
    counts = models.JSONField(default=dict)  # Measurement counts from multiple shots
    shots = models.IntegerField(default=1024)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Simulation for {self.circuit.title}"

class QASession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='qa_sessions')
    circuit = models.ForeignKey(QuantumCircuit, on_delete=models.CASCADE, null=True, blank=True)
    question = models.TextField()
    answer = models.TextField()
    context_gates = models.JSONField(default=list, blank=True)  # Relevant gates for context
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Q: {self.question[:50]}..."

class QuizQuestion(models.Model):
    circuit = models.ForeignKey(QuantumCircuit, on_delete=models.CASCADE, related_name='quizzes')
    question = models.TextField()
    options = models.JSONField()  # List of answer options
    correct_answer = models.IntegerField()  # Index of correct answer
    explanation = models.TextField()
    difficulty_level = models.CharField(max_length=20, choices=User.DIFFICULTY_LEVELS)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Quiz for {self.circuit.title}"