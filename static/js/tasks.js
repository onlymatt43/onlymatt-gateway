// Tasks functionality
let tasks = [];

document.getElementById('task-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const data = {
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-description').value,
        priority: document.getElementById('task-priority').value
    };

    try {
        const response = await fetch('/admin/tasks', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-OM-Key': 'test_key' // In production, get from secure source
            },
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
        const response = await fetch('/admin/tasks', {
            headers: {
                'X-OM-Key': 'test_key'
            }
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
        const response = await fetch(`/admin/tasks/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-OM-Key': 'test_key'
            },
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
        const response = await fetch(`/admin/tasks/${id}`, {
            method: 'DELETE',
            headers: {
                'X-OM-Key': 'test_key'
            }
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