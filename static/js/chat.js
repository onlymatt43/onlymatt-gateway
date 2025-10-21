// Chat functionality
let chatMessages = document.getElementById('chat-messages');
let messageInput = document.getElementById('message-input');
let temperatureSlider = document.getElementById('temperature');
let tempValue = document.getElementById('temp-value');

temperatureSlider.addEventListener('input', function() {
    tempValue.textContent = this.value;
});

async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message) return;

    // Add user message
    addMessage('user', message);
    messageInput.value = '';

    try {
        const response = await fetch('/ai/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: document.getElementById('model-select').value,
                prompt: message,
                temperature: parseFloat(temperatureSlider.value),
                stream: false
            })
        });

        const data = await response.json();

        if (response.ok) {
            addMessage('assistant', data.response || 'Réponse reçue');
        } else {
            addMessage('assistant', 'Erreur: ' + (data.error || 'Erreur inconnue'));
        }
    } catch (error) {
        addMessage('assistant', 'Erreur de connexion: ' + error.message);
    }
}

function addMessage(sender, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    messageDiv.innerHTML = `<strong>${sender === 'user' ? 'Vous' : 'Assistant'}:</strong> ${content}`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Enter key to send
messageInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});