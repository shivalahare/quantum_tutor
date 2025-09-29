import tempfile
import base64
from io import StringIO
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator, Aer
from qiskit.quantum_info import Statevector
import json
import traceback

class CircuitParser:
    @staticmethod
    def parse_qiskit_code(qiskit_code):
        """Parse Qiskit code and extract circuit information"""
        try:
            # Create a temporary module to execute the code
            local_vars = {}
            exec(qiskit_code, {}, local_vars)
            
            # Find QuantumCircuit objects in the local variables
            circuits = {}
            for var_name, var_value in local_vars.items():
                if isinstance(var_value, QuantumCircuit):
                    circuits[var_name] = var_value
            
            if not circuits:
                raise ValueError("No QuantumCircuit object found in the code. Make sure you create a QuantumCircuit instance (e.g., qc = QuantumCircuit(2)).")
            
            # Use the first circuit found
            circuit_name, circuit = next(iter(circuits.items()))
            return circuit
            
        except Exception as e:
            error_details = traceback.format_exc()
            raise ValueError(f"Error parsing Qiskit code: {str(e)}\n\nDebug info:\n{error_details}")
    
    @staticmethod
    def extract_gates_from_circuit(circuit):
        """Extract gate information from a QuantumCircuit object"""
        gates = []
        step_order = 0
        
        try:
            for instruction in circuit.data:
                gate_info = {
                    'gate_type': instruction.operation.name,
                    'qubits': [circuit.find_bit(qubit).index for qubit in instruction.qubits],
                    'step_order': step_order,
                    'parameters': {}
                }
                
                # Extract parameters for parameterized gates
                if hasattr(instruction.operation, 'params') and instruction.operation.params:
                    gate_info['parameters'] = {
                        'params': [float(p) for p in instruction.operation.params]
                    }
                
                gates.append(gate_info)
                step_order += 1
        except Exception as e:
            raise ValueError(f"Error extracting gates: {str(e)}")
        
        return gates
    
    @staticmethod
    def generate_circuit_diagram(circuit):
        """Generate text diagram of the circuit"""
        try:
            # Generate text representation
            text_diagram = str(circuit)
            return f"<pre class='font-mono text-sm'>{text_diagram}</pre>"
        except Exception as e:
            return f"<pre>Error generating diagram: {str(e)}</pre>"

class CircuitSimulator:
    def __init__(self):
        self.simulator = AerSimulator()
        self.statevector_simulator = Aer.get_backend('statevector_simulator')
    
    def simulate_statevector(self, circuit):
        """Simulate circuit and return statevector using multiple methods"""
        try:
            # Method 1: Use Statevector directly from the circuit
            try:
                # Remove measurements for statevector calculation
                statevector_circuit = circuit.copy()
                statevector_circuit.remove_final_measurements()
                
                # Get statevector directly
                statevector = Statevector.from_instruction(statevector_circuit)
                
                # Convert to JSON-serializable format
                statevector_json = []
                for i, amplitude in enumerate(statevector):
                    statevector_json.append({
                        'state': format(i, f'0{circuit.num_qubits}b'),
                        'amplitude_real': float(amplitude.real),
                        'amplitude_imag': float(amplitude.imag),
                        'probability': float(abs(amplitude)**2)
                    })
                
                return statevector_json
                
            except Exception as e:
                
                # Method 2: Use statevector simulator backend directly
                statevector_circuit = circuit.copy()
                statevector_circuit.remove_final_measurements()
                
                # Use statevector simulator
                backend = Aer.get_backend('statevector_simulator')
                job = backend.run(transpile(statevector_circuit, backend))
                result = job.result()
                
                # Get the statevector
                statevector = result.get_statevector()
                
                # Convert to JSON-serializable format
                statevector_json = []
                for i, amplitude in enumerate(statevector):
                    statevector_json.append({
                        'state': format(i, f'0{circuit.num_qubits}b'),
                        'amplitude_real': float(amplitude.real),
                        'amplitude_imag': float(amplitude.imag),
                        'probability': float(abs(amplitude)**2)
                    })
                
                return statevector_json
                
        except Exception as e:
            error_details = traceback.format_exc()
            raise ValueError(f"Statevector simulation failed: {str(e)}\n\nDebug info:\n{error_details}")
    
    def simulate_measurements(self, circuit, shots=1024):
        """Simulate measurements and return probabilities"""
        try:
            # Create a copy to avoid modifying the original
            measurement_circuit = circuit.copy()
            
            # Make sure circuit has measurements
            if not any(gate.name == 'measure' for gate in measurement_circuit.data):
                measurement_circuit.measure_all()
            
            # Use AerSimulator for measurement simulation
            backend = AerSimulator()
            transpiled_circuit = transpile(measurement_circuit, backend)
            
            # Run simulation
            job = backend.run(transpiled_circuit, shots=shots)
            result = job.result()
            counts = result.get_counts()
            
            # Calculate probabilities
            probabilities = {state: count/shots for state, count in counts.items()}
            
            return probabilities, counts
            
        except Exception as e:
            error_details = traceback.format_exc()
            raise ValueError(f"Measurement simulation failed: {str(e)}\n\nDebug info:\n{error_details}")