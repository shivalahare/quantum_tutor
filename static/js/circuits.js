// Circuit creation and management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initializeCircuitForm();
    initializeCodeEditor();
});

function initializeCircuitForm() {
    const form = document.getElementById('circuitForm');
    const previewBtn = document.getElementById('previewBtn');
    
    form.addEventListener('submit', handleCircuitSubmit);
    previewBtn.addEventListener('click', handlePreview);
}

function initializeCodeEditor() {
    const codeEditor = document.getElementById('qiskit_code');
    
    // Add basic syntax highlighting
    codeEditor.addEventListener('input', function() {
        // Simple Python syntax highlighting
        const code = this.value;
        // This would be enhanced with a proper code editor library
    });
}

async function handleCircuitSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const title = document.getElementById('title').value;
    const qiskitCode = document.getElementById('qiskit_code').value;
    
    if (!title || !qiskitCode) {
        showToast('Please fill in all fields', 'error');
        return;
    }
    
    setLoading(submitBtn, true);
    
    try {
        const response = await fetch('/api/circuits/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                title: title,
                qiskit_code: qiskitCode
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Circuit created successfully!', 'success');
            setTimeout(() => {
                window.location.href = `/circuits/${data.id}/`;
            }, 1000);
        } else {
            throw new Error(data.error || 'Failed to create circuit');
        }
    } catch (error) {
        console.error('Error creating circuit:', error);
        showToast('Error creating circuit: ' + error.message, 'error');
    } finally {
        setLoading(submitBtn, false);
    }
}

async function handlePreview() {
    const title = document.getElementById('title').value;
    const qiskitCode = document.getElementById('qiskit_code').value;
    const previewBtn = document.getElementById('previewBtn');
    
    if (!title || !qiskitCode) {
        showToast('Please enter both title and Qiskit code', 'warning');
        return;
    }
    
    setLoading(previewBtn, true);
    
    try {
        // Simulate preview generation
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        document.getElementById('circuitDiagram').innerHTML = `
            <div class="preview-placeholder">
                <div class="placeholder-icon">🔬</div>
                <p>Preview Generated</p>
                <small>Circuit visualization will be available after creation</small>
            </div>
        `;
        
        // Simulate gate detection
        const gates = detectGatesFromCode(qiskitCode);
        updateGateList(gates);
        
        showToast('Preview generated successfully', 'success');
    } catch (error) {
        showToast('Error generating preview', 'error');
    } finally {
        setLoading(previewBtn, false);
    }
}

function detectGatesFromCode(code) {
    // Simple gate detection from Qiskit code
    const gates = [];
    const gatePatterns = {
        'h': /\.h\(([^)]+)\)/g,
        'x': /\.x\(([^)]+)\)/g,
        'cx': /\.cx\(([^)]+)\)/g,
        'measure': /\.measure\(([^)]+)\)/g
    };
    
    for (const [gateType, pattern] of Object.entries(gatePatterns)) {
        const matches = code.matchAll(pattern);
        for (const match of matches) {
            gates.push({
                type: gateType,
                qubits: match[1],
                parameters: {}
            });
        }
    }
    
    return gates;
}

function updateGateList(gates) {
    const container = document.querySelector('.gates-container');
    
    if (gates.length === 0) {
        container.innerHTML = '<div class="gate-placeholder">No gates detected in code</div>';
        return;
    }
    
    container.innerHTML = gates.map(gate => `
        <div class="gate-item">
            <span class="gate-type">${gate.type.toUpperCase()}</span>
            <span class="gate-qubits">Qubits: ${gate.qubits}</span>
            ${gate.parameters ? `<span class="gate-params">${JSON.stringify(gate.parameters)}</span>` : ''}
        </div>
    `).join('');
}

function formatCode() {
    const editor = document.getElementById('qiskit_code');
    const code = editor.value;
    
    // Simple formatting - in production, use a proper formatter
    const formatted = code
        .replace(/\n\s*\n/g, '\n\n') // Remove multiple empty lines
        .replace(/^(\s*)#/gm, '$1# ') // Ensure space after comment
        .trim();
    
    editor.value = formatted;
    showToast('Code formatted', 'success');
}

function clearCode() {
    if (confirm('Are you sure you want to clear the code editor?')) {
        document.getElementById('qiskit_code').value = '';
        showToast('Code cleared', 'info');
    }
}

function loadExample(exampleType) {
    const examples = {
        bell_state: `from qiskit import QuantumCircuit

# Create Bell state (maximally entangled state)
qc = QuantumCircuit(2, 2)

# Create superposition on first qubit
qc.h(0)

# Entangle the qubits
qc.cx(0, 1)

# Measure both qubits
qc.measure([0, 1], [0, 1])`,

        superposition: `from qiskit import QuantumCircuit

# Simple superposition example
qc = QuantumCircuit(1, 1)

# Put qubit in superposition
qc.h(0)

# Measure the qubit
qc.measure(0, 0)`,

        quantum_teleportation: `from qiskit import QuantumCircuit

# Quantum teleportation protocol
qc = QuantumCircuit(3, 3)

# Create entanglement between qubit 1 and 2
qc.h(1)
qc.cx(1, 2)

# Prepare the state to teleport (qubit 0)
qc.x(0)  # |1> state

# Teleportation protocol
qc.cx(0, 1)
qc.h(0)
qc.measure([0, 1], [0, 1])
qc.cx(1, 2)
qc.cz(0, 2)`
    };
    
    if (examples[exampleType]) {
        document.getElementById('qiskit_code').value = examples[exampleType];
        document.getElementById('title').value = exampleType.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
        showToast('Example loaded', 'success');
    }
}