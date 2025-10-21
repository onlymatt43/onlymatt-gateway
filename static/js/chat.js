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
    const userMessage = message;
    messageInput.value = '';

    try {
        const response = await fetch('/ai/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model: document.getElementById('model-select').value,
                prompt: userMessage,
                temperature: parseFloat(temperatureSlider.value),
                stream: false
            })
        });

        const data = await response.json();

        if (response.ok) {
            const assistantResponse = data.response || 'Réponse reçue';
            addMessage('assistant', assistantResponse);

            // Save to Turso
            await saveChatHistory(userMessage, assistantResponse);
        } else {
            addMessage('assistant', 'Erreur: ' + (data.error || 'Erreur inconnue'));
        }
    } catch (error) {
        addMessage('assistant', 'Erreur de connexion: ' + error.message);
    }
}

async function saveChatHistory(userMessage, assistantResponse) {
    try {
        const response = await fetch('/admin/chat/history', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-OM-Key': 'test_key'
            },
            body: JSON.stringify({
                user_message: userMessage,
                assistant_response: assistantResponse,
                model: document.getElementById('model-select').value,
                temperature: parseFloat(temperatureSlider.value)
            })
        });

        if (!response.ok) {
            console.error('Erreur sauvegarde chat');
        }
    } catch (error) {
        console.error('Erreur connexion sauvegarde chat:', error);
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