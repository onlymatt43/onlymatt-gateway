// Tasks functionality
let tasks = JSON.parse(localStorage.getItem('admin_tasks') || '[]');

document.getElementById('task-form').addEventListener('submit', function(e) {
    e.preventDefault();

    const task = {
        id: Date.now(),
        title: document.getElementById('task-title').value,
        description: document.getElementById('task-description').value,
        priority: document.getElementById('task-priority').value,
        status: 'pending',
        created: new Date().toISOString()
    };

    tasks.push(task);
    saveTasks();
    renderTasks();
    updateStats();

    document.getElementById('task-form').reset();
});

function saveTasks() {
    localStorage.setItem('admin_tasks', JSON.stringify(tasks));
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
                    <small class="text-muted">Créé: ${new Date(task.created).toLocaleDateString()}</small>
                </div>
                <div>
                    <button class="btn btn-sm btn-outline-success me-1" onclick="completeTask(${task.id})">✓</button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteTask(${task.id})">×</button>
                </div>
            </div>
        `;
        tasksList.appendChild(taskDiv);
    });
}

function completeTask(id) {
    const task = tasks.find(t => t.id === id);
    if (task) {
        task.status = task.status === 'completed' ? 'pending' : 'completed';
        saveTasks();
        renderTasks();
        updateStats();
    }
}

function deleteTask(id) {
    tasks = tasks.filter(t => t.id !== id);
    saveTasks();
    renderTasks();
    updateStats();
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
renderTasks();
updateStats();