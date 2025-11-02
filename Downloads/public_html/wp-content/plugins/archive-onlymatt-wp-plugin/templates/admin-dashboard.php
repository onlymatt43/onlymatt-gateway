<div class="wrap onlymatt-admin-wrap">
    <h1>ONLYMATT AI - Tableau de Bord</h1>

    <h2 class="nav-tab-wrapper">
        <a href="#dashboard" class="nav-tab nav-tab-active">Tableau de Bord</a>
        <a href="#chat" class="nav-tab">Chat</a>
        <a href="#tasks" class="nav-tab">Tâches</a>
        <a href="#settings" class="nav-tab">Paramètres</a>
    </h2>

    <div id="dashboard-content">
        <div class="onlymatt-dashboard">
            <div class="dashboard-card">
                <h3>Statut du Système</h3>
                <div class="dashboard-stat">
                    <span>Connexion API:</span>
                    <span class="status-indicator" id="api-status">Vérification...</span>
                </div>
                <div class="dashboard-stat">
                    <span>Messages aujourd'hui:</span>
                    <span class="number" id="messages-today">0</span>
                </div>
                <div class="dashboard-stat">
                    <span>Tâches actives:</span>
                    <span class="number" id="active-tasks">0</span>
                </div>
            </div>

            <div class="dashboard-card">
                <h3>Actions Rapides</h3>
                <p><button class="button button-primary" onclick="testConnection()">Tester la Connexion</button></p>
                <p><button class="button" onclick="clearCache()">Vider le Cache</button></p>
                <p><button class="button" onclick="exportData()">Exporter les Données</button></p>
            </div>

            <div class="dashboard-card">
                <h3>Informations Système</h3>
                <p><strong>Version Plugin:</strong> 1.0.0</p>
                <p><strong>URL API:</strong> <span id="api-url"><?php echo get_option('onlymatt_api_base', 'https://onlymatt-gateway.onrender.com'); ?></span></p>
                <p><strong>Dernière synchro:</strong> <span id="last-sync">Jamais</span></p>
            </div>
        </div>
    </div>
</div>

<script>
function testConnection() {
    jQuery.ajax({
        url: onlymatt_ajax.ajax_url,
        type: 'POST',
        data: {
            action: 'onlymatt_chat',
            message: 'test',
            nonce: onlymatt_ajax.nonce
        },
        success: function(response) {
            if (response.success) {
                alert('Connexion réussie !');
                jQuery('#api-status').text('OK').css('color', 'green');
            } else {
                alert('Erreur de connexion: ' + response.data);
                jQuery('#api-status').text('Erreur').css('color', 'red');
            }
        },
        error: function() {
            alert('Erreur de connexion au serveur');
            jQuery('#api-status').text('Erreur').css('color', 'red');
        }
    });
}

function clearCache() {
    if (confirm('Vider le cache ?')) {
        localStorage.clear();
        alert('Cache vidé');
    }
}

function exportData() {
    // Placeholder for export functionality
    alert('Fonctionnalité d\'export à implémenter');
}
</script>