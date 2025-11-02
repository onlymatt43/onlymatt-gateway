// Tasks functionality
let tasks = [];

function getAdminHeaders(extraHeaders, message) {
    try {
        if (window.omAdminHeaders) {
            return window.omAdminHeaders(extraHeaders);
        }
    } catch (error) {
        if (error && (error.code === 'missing_admin_key' || error.message === 'missing_admin_key')) {
            alert(message || 'Cette action nécessite une clé administrateur.');
            return null;
        }
        throw error;
    }

    const key = window.prompt('Entrez la clé administrateur (X-OM-Key)');
    if (!key) {
        alert(message || 'Cette action nécessite une clé administrateur.');
        return null;
    }
    if (window.omSetAdminKey) {
        window.omSetAdminKey(key);
    }
    return Object.assign({}, extraHeaders || {}, { 'X-OM-Key': key.trim() });
}

document.getElementById('task-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const data = {
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-description').value,
        priority: document.getElementById('task-priority').value
    };

    try {
        const headers = getAdminHeaders({
            'Content-Type': 'application/json'
        }, 'Veuillez fournir votre clé administrateur pour ajouter une tâche.');

        if (!headers) {
            return;
        }

        const response = await fetch('/admin/tasks', {
            method: 'POST',
            headers,
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (response.ok) {
            alert('Tâche ajoutée avec succès!');
            document.getElementById('task-form').reset();
            loadTasks();
        } else {
            alert('Erreur: ' + (result.err || 'Erreur inconnue'));
        }
    } catch (error) {
        alert('Erreur de connexion: ' + error.message);
    }
});

async function loadTasks() {
    try {
        const headers = getAdminHeaders({}, 'Veuillez fournir votre clé administrateur pour consulter les tâches.');
        if (!headers) {
            document.getElementById('tasks-list').innerHTML = '<p class="text-danger">Clé administrateur requise.</p>';
            return;
        }

        const response = await fetch('/admin/tasks', {
            headers
        });
        const data = await response.json();

        if (data.ok) {
            tasks = data.tasks;
            renderTasks();
            updateStats();
        } else {
            console.error('Erreur chargement tâches:', data.err);
        }
    } catch (error) {
        console.error('Erreur connexion:', error);
    }
}

function renderTasks() {
    const tasksList = document.getElementById('tasks-list');
    tasksList.innerHTML = '';

    tasks.forEach(task => {
        const taskDiv = document.createElement('div');
        taskDiv.className = `task-item ${task.priority} ${task.status}`;
        taskDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <h6 class="mb-1">${task.title}</h6>
                    <p class="mb-1">${task.description}</p>
                    <small class="text-muted">Créé: ${new Date(task.created_at).toLocaleDateString()}</small>
                </div>
                <div>
                    <button class="btn btn-sm btn-outline-success me-1" onclick="completeTask('${task.id}')">✓</button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteTask('${task.id}')">×</button>
                </div>
            </div>
        `;
        tasksList.appendChild(taskDiv);
    });
}

async function completeTask(id) {
    try {
        const headers = getAdminHeaders({
            'Content-Type': 'application/json'
        }, 'Veuillez fournir votre clé administrateur pour mettre à jour une tâche.');
        if (!headers) {
            return;
        }

        const response = await fetch(`/admin/tasks/${id}`, {
            method: 'PUT',
            headers,
            body: JSON.stringify({ status: 'completed' })
        });

        if (response.ok) {
            loadTasks();
        } else {
            alert('Erreur lors de la mise à jour');
        }
    } catch (error) {
        alert('Erreur de connexion: ' + error.message);
    }
}

async function deleteTask(id) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette tâche ?')) return;

    try {
        const headers = getAdminHeaders({}, 'Veuillez fournir votre clé administrateur pour supprimer une tâche.');
        if (!headers) {
            return;
        }

        const response = await fetch(`/admin/tasks/${id}`, {
            method: 'DELETE',
            headers
        });

        if (response.ok) {
            loadTasks();
        } else {
            alert('Erreur lors de la suppression');
        }
    } catch (error) {
        alert('Erreur de connexion: ' + error.message);
    }
}

function updateStats() {
    const total = tasks.length;
    const pending = tasks.filter(t => t.status === 'pending').length;
    const completed = tasks.filter(t => t.status === 'completed').length;

    document.getElementById('total-tasks').textContent = total;
    document.getElementById('pending-tasks').textContent = pending;
    document.getElementById('completed-tasks').textContent = completed;
}

// Load tasks on page load
loadTasks();