// Education functionality
document.getElementById('memory-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const data = {
        user_id: document.getElementById('user_id').value,
        persona: document.getElementById('persona').value,
        key: document.getElementById('key').value,
        value: document.getElementById('value').value,
        confidence: parseFloat(document.getElementById('confidence').value),
        ttl_days: 180
    };

    try {
        const response = await fetch('/ai/memory/remember', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            alert('Mémoire ajoutée avec succès!');
            document.getElementById('memory-form').reset();
            loadMemories();
        } else {
            alert('Erreur: ' + (result.err || 'Erreur inconnue'));
        }
    } catch (error) {
        alert('Erreur de connexion: ' + error.message);
    }
});

async function loadMemories() {
    try {
        const response = await fetch('/ai/memory/recall?user_id=admin&persona=coach_v1&limit=10');
        const data = await response.json();

        const memoriesList = document.getElementById('memories-list');
        memoriesList.innerHTML = '';

        if (data.memories && data.memories.length > 0) {
            data.memories.forEach(memory => {
                const memoryDiv = document.createElement('div');
                memoryDiv.className = 'border rounded p-2 mb-2';
                memoryDiv.innerHTML = `
                    <strong>${memory.key}</strong><br>
                    <small class="text-muted">${memory.created_at}</small><br>
                    ${memory.value}
                `;
                memoriesList.appendChild(memoryDiv);
            });
        } else {
            memoriesList.innerHTML = '<p class="text-muted">Aucune mémoire trouvée.</p>';
        }
    } catch (error) {
        document.getElementById('memories-list').innerHTML = '<p class="text-danger">Erreur de chargement: ' + error.message + '</p>';
    }
}

function addPrompt(type, content) {
    document.getElementById('key').value = type;
    document.getElementById('value').value = content;
}

// Load memories on page load
loadMemories();