from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse
from .models import (
    User, QuantumCircuit, CircuitGate, Explanation, 
    SimulationResult, QASession, QuizQuestion
)
from .serializers import (
    QuantumCircuitSerializer, CircuitGateSerializer,
    SimulationResultSerializer, QASessionSerializer,
    QuizQuestionSerializer
)
from .qiskit_utils import CircuitParser, CircuitSimulator
from .ai_tutor import AITutor

@login_required
def dashboard(request):
    """Main dashboard view"""
    circuits = QuantumCircuit.objects.filter(user=request.user)
    return render(request, 'tutor/dashboard.html', {'circuits': circuits})

@login_required
def circuit_create(request):
    """Create a new quantum circuit"""
    if request.method == 'POST':
        title = request.POST.get('title')
        qiskit_code = request.POST.get('qiskit_code')
        
        if title and qiskit_code:
            circuit = QuantumCircuit.objects.create(
                user=request.user,
                title=title,
                qiskit_code=qiskit_code
            )
            return JsonResponse({'circuit_id': circuit.id})
    
    return render(request, 'tutor/circuit_create.html')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_circuit_api(request):
    """API endpoint for creating circuits"""
    try:
        title = request.data.get('title')
        qiskit_code = request.data.get('qiskit_code')
        
        if not title or not qiskit_code:
            return Response(
                {'error': 'Title and Qiskit code are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        circuit = QuantumCircuit.objects.create(
            user=request.user,
            title=title,
            qiskit_code=qiskit_code
        )
        
        serializer = QuantumCircuitSerializer(circuit)
        return Response({
            'status': 'Circuit created successfully',
            'circuit_id': circuit.id,
            'circuit': serializer.data
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@login_required
def circuit_detail(request, circuit_id):
    """Circuit detail view"""
    circuit = get_object_or_404(QuantumCircuit, id=circuit_id, user=request.user)
    return render(request, 'tutor/circuit_detail.html', {'circuit': circuit})

class QuantumCircuitViewSet(viewsets.ModelViewSet):
    serializer_class = QuantumCircuitSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return QuantumCircuit.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def parse_circuit(self, request, pk=None):
        """Parse Qiskit code and extract gates - SILENT VERSION"""
        circuit = self.get_object()
        
        # Check if user owns this circuit
        if circuit.user != request.user:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        parser = CircuitParser()
        
        try:
            # Parse the Qiskit code (this will now be silent)
            qiskit_circuit = parser.parse_qiskit_code(circuit.qiskit_code)
            
            # Update circuit information
            circuit.num_qubits = qiskit_circuit.num_qubits
            circuit.num_classical_bits = qiskit_circuit.num_clbits
            
            # Generate circuit diagram
            circuit.circuit_diagram_svg = parser.generate_circuit_diagram(qiskit_circuit)
            circuit.save()
            
            # Clear existing gates
            circuit.gates.all().delete()
            
            # Create new gates
            gates_data = parser.extract_gates_from_circuit(qiskit_circuit)
            for gate_data in gates_data:
                CircuitGate.objects.create(circuit=circuit, **gate_data)
            
            return Response({
                'status': 'Circuit parsed successfully',
                'num_qubits': circuit.num_qubits,
                'num_gates': len(gates_data)
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
    @action(detail=True, methods=['post'])
    def execute_code(self, request, pk=None):
        """Execute user Qiskit code and return results including plots"""
        circuit = self.get_object()
        
        # Check if user owns this circuit
        if circuit.user != request.user:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        simulator = CircuitSimulator()
        
        try:
            # Execute user code
            result = simulator.execute_user_code(circuit.qiskit_code)
            
            return Response({
                'status': 'Code executed successfully',
                'text_output': result['text_output'],
                'plots': result['plots'],
                'has_circuit': result['circuit'] is not None,
                'statevector': result.get('statevector'),
                'counts': result.get('counts')
            })
            
        except Exception as e:
            error_message = str(e)
            return Response(
                {'error': error_message}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
    @action(detail=True, methods=['post'])
    def simulate(self, request, pk=None):
        """Run simulation on the circuit"""
        circuit = self.get_object()
        
        # Check if user owns this circuit
        if circuit.user != request.user:
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        simulator = CircuitSimulator()
        parser = CircuitParser()
        
        try:
            # Parse circuit first
            qiskit_circuit = parser.parse_qiskit_code(circuit.qiskit_code)
            
            # Validate circuit has qubits
            if qiskit_circuit.num_qubits == 0:
                return Response(
                    {'error': 'Circuit has no qubits. Please check your Qiskit code.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update circuit information if needed
            if circuit.num_qubits != qiskit_circuit.num_qubits:
                circuit.num_qubits = qiskit_circuit.num_qubits
                circuit.num_classical_bits = qiskit_circuit.num_clbits
                circuit.save()
            
            # Run simulations
            statevector = simulator.simulate_statevector(qiskit_circuit)
            probabilities, counts = simulator.simulate_measurements(qiskit_circuit, shots=1024)
            
            # Validate simulation results
            if not statevector:
                return Response(
                    {'error': 'Statevector simulation returned no results. The circuit might be too complex or contain unsupported operations.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not probabilities:
                return Response(
                    {'error': 'Measurement simulation returned no results.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save results
            simulation_result, created = SimulationResult.objects.update_or_create(
                circuit=circuit,
                defaults={
                    'statevector': statevector,
                    'probabilities': probabilities,
                    'counts': counts,
                    'shots': 1024
                }
            )
            
            serializer = SimulationResultSerializer(simulation_result)
            return Response({
                'status': 'Simulation completed successfully',
                'statevector_count': len(statevector),
                'probability_count': len(probabilities),
                'results': serializer.data
            })
            
        except Exception as e:
            error_message = str(e)
            # Log the full error for debugging

            # Provide more user-friendly error messages
            if "statevector" in error_message.lower():
                error_message = "Statevector simulation failed. This might be due to measurement operations in the circuit or unsupported gates."
            elif "measurement" in error_message.lower():
                error_message = "Measurement simulation failed. Please check your circuit for errors."
            
            return Response(
                {'error': error_message}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def get_explanations(self, request, pk=None):
        """Get AI explanations for all gates in the circuit"""
        circuit = self.get_object()
        tutor = AITutor()
        explanations = []
        
        for gate in circuit.gates.all():
            explanation = tutor.generate_gate_explanation(
                gate.gate_type,
                request.user.difficulty_level,
                [g.gate_type for g in circuit.gates.all() if g.step_order < gate.step_order]
            )
            explanations.append({
                'gate': gate.gate_type,
                'qubits': gate.qubits,
                'step_order': gate.step_order,
                'explanation': explanation
            })
        
        return Response(explanations)

class QASessionViewSet(viewsets.ModelViewSet):
    serializer_class = QASessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return QASession.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def ask_question(self, request):
        """Ask a question to the AI tutor"""
        question = request.data.get('question')
        circuit_id = request.data.get('circuit_id')
        
        if not question:
            return Response(
                {'error': 'Question is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tutor = AITutor()
        circuit_context = None
        
        if circuit_id:
            try:
                circuit = QuantumCircuit.objects.get(id=circuit_id, user=request.user)
                circuit_context = {
                    'num_qubits': circuit.num_qubits,
                    'gates': [gate.gate_type for gate in circuit.gates.all()],
                    'purpose': circuit.title
                }
            except QuantumCircuit.DoesNotExist:
                pass
        
        try:
            answer = tutor.answer_question(question, circuit_context, request.user.difficulty_level)
        except Exception as e:
            answer = f"AI service error: {str(e)}"
        
        # Save Q&A session
        qa_session = QASession.objects.create(
            user=request.user,
            circuit_id=circuit_id,
            question=question,
            answer=answer,
            context_gates=circuit_context['gates'] if circuit_context else []
        )
        
        return Response({
            'question': question,
            'answer': answer,
            'session_id': qa_session.id
        })

class QuizQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuizQuestionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return QuizQuestion.objects.filter(circuit__user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def generate_quiz(self, request, pk=None):
        """Generate a quiz question for the circuit"""
        circuit = get_object_or_404(QuantumCircuit, id=pk, user=request.user)
        tutor = AITutor()
        
        quiz_data = tutor.generate_quiz_question(circuit, request.user.difficulty_level)
        
        quiz_question = QuizQuestion.objects.create(
            circuit=circuit,
            question=quiz_data['question'],
            options=quiz_data['options'],
            correct_answer=quiz_data['correct_answer'],
            explanation=quiz_data['explanation'],
            difficulty_level=request.user.difficulty_level
        )
        
        serializer = self.get_serializer(quiz_question)
        return Response(serializer.data)

# Additional function-based views for web interface
@login_required
def simulation_view(request, circuit_id):
    """Simulation results view"""
    circuit = get_object_or_404(QuantumCircuit, id=circuit_id, user=request.user)
    simulation = getattr(circuit, 'simulation', None)
    return render(request, 'tutor/simulation.html', {
        'circuit': circuit,
        'simulation': simulation
    })

@login_required
def qa_view(request):
    """Q&A session view"""
    qa_sessions = QASession.objects.filter(user=request.user).order_by('-created_at')[:10]
    circuits = QuantumCircuit.objects.filter(user=request.user)
    
    if request.method == 'POST':
        question = request.POST.get('question')
        circuit_id = request.POST.get('circuit_id')
        
        if question:
            # Use the OpenRouter tutor directly
            tutor = AITutor()
            circuit_context = None
            
            if circuit_id:
                try:
                    circuit = QuantumCircuit.objects.get(id=circuit_id, user=request.user)
                    circuit_context = {
                        'num_qubits': circuit.num_qubits,
                        'gates': [gate.gate_type for gate in circuit.gates.all()],
                        'purpose': circuit.title
                    }
                except QuantumCircuit.DoesNotExist:
                    pass
            
            # Get AI answer
            answer = tutor.answer_question(question, circuit_context, request.user.difficulty_level)
            
            # Save Q&A session
            qa_session = QASession.objects.create(
                user=request.user,
                circuit_id=circuit_id,
                question=question,
                answer=answer,
                context_gates=circuit_context['gates'] if circuit_context else []
            )
            
            # Return the same page with the new Q&A session
            return render(request, 'tutor/qa_session.html', {
                'qa_sessions': QASession.objects.filter(user=request.user).order_by('-created_at')[:10],
                'circuits': circuits,
                'new_question': question,
                'new_answer': answer
            })
    
    return render(request, 'tutor/qa_session.html', {
        'qa_sessions': qa_sessions,
        'circuits': circuits
    })

