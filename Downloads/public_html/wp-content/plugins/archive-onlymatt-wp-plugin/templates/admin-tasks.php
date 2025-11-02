<div class="wrap onlymatt-admin-wrap">
    <h1>ONLYMATT AI - Gestion des Tâches</h1>

    <div id="task-form" style="background: #f9f9f9; padding: 15px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 20px;">
        <h3>Créer une Nouvelle Tâche</h3>
        <input type="text" id="task-title" placeholder="Titre de la tâche" style="width: 100%; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px;" />
        <textarea id="task-description" placeholder="Description de la tâche" style="width: 100%; min-height: 80px; padding: 8px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px;"></textarea>
        <select id="task-priority" style="margin-bottom: 10px; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            <option value="low">Faible</option>
            <option value="medium" selected>Moyenne</option>
            <option value="high">Élevée</option>
        </select>
        <button id="create-task" class="button button-primary">Créer la Tâche</button>
    </div>

    <div id="tasks-list">
        <!-- Tasks will be loaded here -->
    </div>
</div>