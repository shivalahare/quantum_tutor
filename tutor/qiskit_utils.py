import tempfile
import base64
from io import BytesIO, StringIO
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator, Aer
from qiskit.quantum_info import Statevector
import json
import traceback
import matplotlib
import warnings
# Set non-interactive backend BEFORE importing pyplot
matplotlib.use('Agg')  # Use Agg backend for non-GUI rendering
import matplotlib.pyplot as plt

# Suppress matplotlib warnings
warnings.filterwarnings("ignore", message=".*FigureCanvasAgg is non-interactive.*")
warnings.filterwarnings("ignore", message=".*Starting a Matplotlib GUI outside of the main thread.*")

class CircuitParser:
    @staticmethod
    def parse_qiskit_code(qiskit_code):
        """Parse Qiskit code and extract circuit information - SILENT VERSION"""
        try:
            # Capture all output during parsing
            import sys
            from io import StringIO
            
            # Redirect stdout and stderr to capture output
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = captured_output = StringIO()
            sys.stderr = captured_errors = StringIO()
            
            # Create a temporary module to execute the code
            local_vars = {}
            
            # Define SILENT plotting functions that don't print
            def silent_plot_histogram(counts, title='Histogram', figsize=(8, 6)):
                """Silent version - just return the circuit without plotting"""
                return "Plot function called during parsing - use Execute Code for plots"
            
            def silent_plt_show():
                """Silent version - do nothing"""
                return ""
            
            # Add silent functions to local vars
            local_vars['plot_histogram'] = silent_plot_histogram
            local_vars['plt'] = type('plt', (), {
                'show': lambda: silent_plt_show(),
                'figure': lambda *args, **kwargs: None,
                'subplots': lambda *args, **kwargs: (None, None),
                'title': lambda *args, **kwargs: None,
                'xlabel': lambda *args, **kwargs: None,
                'ylabel': lambda *args, **kwargs: None,
                'legend': lambda *args, **kwargs: None,
                'grid': lambda *args, **kwargs: None
            })()
            
            # Override print to be silent during parsing
            original_print = __builtins__['print']
            local_vars['print'] = lambda *args, **kwargs: None
            
            try:
                # Execute the user's code silently
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
                
            finally:
                # Restore stdout and stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                # Discard any captured output during parsing
                _ = captured_output.getvalue()
                _ = captured_errors.getvalue()
            
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
    
    def execute_user_code(self, qiskit_code):
        """Execute user Qiskit code and return results including plots"""
        try:
            output_data = {
                'text_output': '',
                'plots': [],
                'circuit': None,
                'statevector': None,
                'counts': None
            }
            
            # Redirect stdout and stderr
            import sys
            from io import StringIO
            
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = captured_output = StringIO()
            sys.stderr = captured_errors = StringIO()
            
            # Create a temporary module to execute the code
            local_vars = {}
            
            # Define safe plotting functions
            def safe_plot_histogram(counts, title='Histogram', figsize=(8, 6)):
                """Handle plot_histogram by converting to base64 image"""
                try:
                    from qiskit.visualization import plot_histogram
                    
                    # Create plot
                    fig = plot_histogram(counts, title=title, figsize=figsize)
                    
                    # Convert to base64
                    buffer = BytesIO()
                    fig.savefig(buffer, format='png', bbox_inches='tight', dpi=100, facecolor='white')
                    buffer.seek(0)
                    image_base64 = base64.b64encode(buffer.getvalue()).decode()
                    plt.close(fig)  # Close the figure to free memory
                    
                    plot_html = f'<div class="plot-container" style="margin: 20px 0; text-align: center;"><h4>{title}</h4><img src="data:image/png;base64,{image_base64}" alt="Histogram" style="max-width: 100%; border: 1px solid #ccc; border-radius: 8px; background: white;"></div>'
                    output_data['plots'].append(plot_html)
                    return f"Plot '{title}' generated successfully"
                    
                except Exception as e:
                    error_msg = f"Plot generation failed: {str(e)}"
                    print(error_msg)
                    return error_msg
            
            def safe_plt_show():
                """Handle plt.show() by returning a message"""
                msg = "Plot displayed below (plt.show() handled by web interface)"
                print(msg)
                return msg
            
            # Add safe functions to local vars
            local_vars['plot_histogram'] = safe_plot_histogram
            local_vars['plt'] = type('plt', (), {
                'show': lambda: safe_plt_show(),
                'figure': plt.figure,
                'subplots': plt.subplots,
                'title': plt.title,
                'xlabel': plt.xlabel,
                'ylabel': plt.ylabel,
                'legend': plt.legend,
                'grid': plt.grid
            })()
            
            try:
                # Execute the user's code
                exec(qiskit_code, {}, local_vars)
                
                # Capture any QuantumCircuit objects and results
                for var_name, var_value in local_vars.items():
                    if isinstance(var_value, QuantumCircuit):
                        output_data['circuit'] = var_name
                    elif var_name == 'statevector' and hasattr(var_value, '__iter__'):
                        output_data['statevector'] = str(var_value)
                    elif var_name == 'counts' and isinstance(var_value, dict):
                        output_data['counts'] = var_value
                        
            except Exception as e:
                # Capture execution errors
                error_msg = f"Execution error: {str(e)}"
                print(error_msg)
            finally:
                # Restore stdout and stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
                # Get captured output
                stdout_content = captured_output.getvalue()
                stderr_content = captured_errors.getvalue()
                
                if stdout_content:
                    output_data['text_output'] += stdout_content
                if stderr_content:
                    output_data['text_output'] += "STDERR: " + stderr_content
            
            return output_data
            
        except Exception as e:
            error_details = traceback.format_exc()
            raise ValueError(f"Error executing user code: {str(e)}\n\nDebug info:\n{error_details}")
    
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
                print(f"Statevector direct method failed: {e}")
                
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