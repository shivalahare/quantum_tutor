// Q&A JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    initializeQAForm();
});

function initializeQAForm() {
    const form = document.getElementById('qaForm');
    form.addEventListener('submit', handleQuestionSubmit);
}

async function handleQuestionSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const question = document.getElementById('question').value;
    const circuitId = document.getElementById('circuit_select').value;
    
    if (!question.trim()) {
        showToast('Please enter a question', 'warning');
        return;
    }
    
    setLoading(submitBtn, true);
    
    try {
        const response = await fetch('/api/qa-sessions/ask_question/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                circuit_id: circuitId || null
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayAnswer(data.question, data.answer);
            addToRecentQuestions(data);
            form.reset();
            showToast('Question answered successfully!', 'success');
        } else {
            throw new Error(data.error || 'Failed to get answer');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error asking question: ' + error.message, 'error');
    } finally {
        setLoading(submitBtn, false);
    }
}

function displayAnswer(question, answer) {
    const answerSection = document.getElementById('answerSection');
    const answerContent = document.getElementById('answerContent');
    
    answerContent.innerHTML = `
        <div class="question-display">
            <h4>Your Question:</h4>
            <p>${question}</p>
        </div>
        <div class="answer-display">
            <h4>AI Tutor Answer:</h4>
            <div class="answer-text">${formatAnswer(answer)}</div>
        </div>
    `;
    
    answerSection.classList.remove('hidden');
    answerSection.scrollIntoView({ behavior: 'smooth' });
}

function formatAnswer(answer) {
    // Convert line breaks to paragraphs and format code blocks
    return answer
        .split('\n\n')
        .map(paragraph => {
            if (paragraph.includes('```')) {
                return `<pre><code>${paragraph.replace(/```/g, '')}</code></pre>`;
            }
            return `<p>${paragraph}</p>`;
        })
        .join('');
}

function addToRecentQuestions(data) {
    const questionsList = document.querySelector('.questions-list');
    
    if (!questionsList) return;
    
    const newQuestionHtml = `
        <div class="question-item" data-session-id="${data.session_id}">
            <div class="question-meta">
                <span class="question-time">just now</span>
            </div>
            <div class="question-text">${data.question.substring(0, 100)}${data.question.length > 100 ? '...' : ''}</div>
            <button onclick="loadSession(${data.session_id})" class="btn-link">
                View Full Conversation
            </button>
        </div>
    `;
    
    questionsList.insertAdjacentHTML('afterbegin', newQuestionHtml);
}

async function loadSession(sessionId) {
    try {
        const response = await fetch(`/api/qa-sessions/${sessionId}/`);
        const data = await response.json();
        
        if (response.ok) {
            showSessionModal(data);
        } else {
            throw new Error('Failed to load session');
        }
    } catch (error) {
        console.error('Error loading session:', error);
        showToast('Error loading conversation', 'error');
    }
}

function showSessionModal(session) {
    const modal = document.getElementById('sessionModal');
    const modalQuestion = document.getElementById('modalQuestion');
    const modalAnswer = document.getElementById('modalAnswer');
    
    modalQuestion.innerHTML = `
        <h4>Question:</h4>
        <p>${session.question}</p>
        ${session.circuit_title ? `<p><small>Circuit: ${session.circuit_title}</small></p>` : ''}
    `;
    
    modalAnswer.innerHTML = `
        <h4>Answer:</h4>
        <div class="answer-text">${formatAnswer(session.answer)}</div>
    `;
    
    modal.classList.remove('hidden');
}

function closeModal() {
    const modal = document.getElementById('sessionModal');
    modal.classList.add('hidden');
}

function copyAnswer() {
    const answerContent = document.getElementById('answerContent');
    const text = answerContent.innerText;
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('Answer copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy answer', 'error');
    });
}

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    const modal = document.getElementById('sessionModal');
    if (e.target === modal) {
        closeModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});