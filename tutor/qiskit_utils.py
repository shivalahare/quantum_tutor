import base64
from io import BytesIO, StringIO
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator, Aer
from qiskit.quantum_info import Statevector
from qiskit.visualization import plot_histogram
import json
import traceback
import matplotlib
# Set non-interactive backend
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys

class CircuitParser:
    @staticmethod
    def parse_qiskit_code(qiskit_code):
        """Parse Qiskit code and extract circuit information - SILENT VERSION"""
        try:
            # Redirect stdout and stderr during parsing
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            
            local_vars = {}
            
            try:
                # Execute silently
                exec(qiskit_code, {}, local_vars)
                
                # Find QuantumCircuit objects
                circuits = {}
                for var_name, var_value in local_vars.items():
                    if isinstance(var_value, QuantumCircuit):
                        circuits[var_name] = var_value
                
                if not circuits:
                    raise ValueError("No QuantumCircuit found in code.")
                
                # Use the first circuit found
                circuit_name, circuit = next(iter(circuits.items()))
                return circuit
                
            finally:
                # Restore and discard output
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
        except Exception as e:
            raise ValueError(f"Error parsing Qiskit code: {str(e)}")
    
    @staticmethod
    def extract_gates_from_circuit(circuit):
        """Extract gate information from a QuantumCircuit object"""
        gates = []
        step_order = 0
        
        for instruction in circuit.data:
            gate_info = {
                'gate_type': instruction.operation.name,
                'qubits': [circuit.find_bit(qubit).index for qubit in instruction.qubits],
                'step_order': step_order,
                'parameters': {}
            }
            
            if hasattr(instruction.operation, 'params') and instruction.operation.params:
                gate_info['parameters'] = {
                    'params': [float(p) for p in instruction.operation.params]
                }
            
            gates.append(gate_info)
            step_order += 1
        
        return gates
    
    @staticmethod
    def generate_circuit_diagram(circuit):
        """Generate text diagram of the circuit"""
        try:
            text_diagram = str(circuit)
            return f"<pre class='font-mono text-sm'>{text_diagram}</pre>"
        except Exception as e:
            return f"<pre>Error generating diagram: {str(e)}</pre>"

class CircuitSimulator:
    def __init__(self):
        self.simulator = AerSimulator()
    
    def execute_user_code(self, qiskit_code):
        """Execute user Qiskit code and return results"""
        # Capture all output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        
        output_data = {
            'text_output': '',
            'plots': [],
            'circuit': None,
            'statevector': None,
            'counts': None
        }
        
        try:
            # Redirect output
            sys.stdout = stdout_capture
            sys.stderr = stderr_capture
            
            # Create local namespace with custom functions
            local_vars = {}
            
            # Custom plot_histogram that returns base64
            def custom_plot_histogram(counts, title='Histogram'):
                try:
                    fig = plot_histogram(counts, title=title)
                    buf = BytesIO()
                    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
                    buf.seek(0)
                    image_base64 = base64.b64encode(buf.getvalue()).decode()
                    plt.close(fig)
                    
                    plot_html = f'<div style="margin: 20px 0; text-align: center;"><h4>{title}</h4><img src="data:image/png;base64,{image_base64}" style="max-width: 100%; border: 1px solid #ccc; border-radius: 8px;"></div>'
                    output_data['plots'].append(plot_html)
                    return "Plot generated"
                except Exception as e:
                    return f"Plot error: {str(e)}"
            
            # PATCH: Replace qiskit.visualization.plot_histogram globally
            import qiskit.visualization
            qiskit.visualization.plot_histogram = custom_plot_histogram
            
            # Custom plt.show that does nothing
            class MockPlt:
                def show(self): 
                    return "Plot displayed in web interface"
                def figure(self, *args, **kwargs): 
                    return None
                def subplots(self, *args, **kwargs): 
                    return (None, None)
                def title(self, *args, **kwargs): 
                    return None
                def xlabel(self, *args, **kwargs): 
                    return None
                def ylabel(self, *args, **kwargs): 
                    return None
            
            # Add custom functions to local vars
            local_vars['plot_histogram'] = custom_plot_histogram
            local_vars['plt'] = MockPlt()
            
            # Execute the code
            exec(qiskit_code, {}, local_vars)
            
            # Capture any results
            for var_name, var_value in local_vars.items():
                if isinstance(var_value, QuantumCircuit):
                    output_data['circuit'] = var_name
                elif var_name == 'statevector':
                    output_data['statevector'] = str(var_value)
                elif var_name == 'counts' and isinstance(var_value, dict):
                    output_data['counts'] = var_value
            
        except Exception as e:
            # Capture errors in output
            print(f"Execution error: {str(e)}")
        finally:
            # Restore stdout/stderr and get captured output
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            
            stdout_content = stdout_capture.getvalue()
            stderr_content = stderr_capture.getvalue()
            
            output_data['text_output'] = stdout_content
            if stderr_content:
                output_data['text_output'] += "\nErrors:\n" + stderr_content
        
        return output_data
    
    def simulate_statevector(self, circuit):
        """Simulate circuit and return statevector"""
        try:
            statevector_circuit = circuit.copy()
            statevector_circuit.remove_final_measurements()
            
            statevector = Statevector.from_instruction(statevector_circuit)
            
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
            raise ValueError(f"Statevector simulation failed: {str(e)}")
    
    def simulate_measurements(self, circuit, shots=1024):
        """Simulate measurements and return probabilities"""
        try:
            measurement_circuit = circuit.copy()
            if not any(gate.name == 'measure' for gate in measurement_circuit.data):
                measurement_circuit.measure_all()
            
            backend = AerSimulator()
            transpiled_circuit = transpile(measurement_circuit, backend)
            job = backend.run(transpiled_circuit, shots=shots)
            result = job.result()
            counts = result.get_counts()
            
            probabilities = {state: count/shots for state, count in counts.items()}
            return probabilities, counts
        except Exception as e:
            raise ValueError(f"Measurement simulation failed: {str(e)}")