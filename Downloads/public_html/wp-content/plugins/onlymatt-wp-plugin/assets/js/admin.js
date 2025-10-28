// ONLYMATT AI Admin JavaScript
jQuery(document).ready(function($) {
    // Chat functionality
    $('#send-message').on('click', function() {
        const message = $('#chat-message').val().trim();
        const persona = $('#chat-persona').val();

        if (!message) return;

        // Add user message
        $('#chat-messages').append('<div class="message user"><strong>Vous:</strong> ' + message + '</div>');

        // Send AJAX
        $.ajax({
            url: onlymatt_ajax.ajax_url,
            type: 'POST',
            data: {
                action: 'onlymatt_chat',
                message: message,
                persona: persona,
                nonce: onlymatt_ajax.nonce
            },
            success: function(response) {
                if (response.success) {
                    const aiResponse = response.data.response || 'Réponse reçue';
                    $('#chat-messages').append('<div class="message ai"><strong>AI:</strong> ' + aiResponse + '</div>');
                } else {
                    $('#chat-messages').append('<div class="message error">Erreur: ' + response.data + '</div>');
                }
                $('#chat-messages').scrollTop($('#chat-messages')[0].scrollHeight);
            },
            error: function() {
                $('#chat-messages').append('<div class="message error">Erreur de connexion</div>');
            }
        });

        $('#chat-message').val('');
    });

    // Tasks functionality
    function loadTasks() {
        $.ajax({
            url: onlymatt_ajax.ajax_url,
            type: 'POST',
            data: {
                action: 'onlymatt_get_tasks',
                nonce: onlymatt_ajax.nonce
            },
            success: function(response) {
                if (response.success) {
                    const tasks = response.data.tasks || [];
                    let html = '';
                    tasks.forEach(function(task) {
                        html += '<div class="task">';
                        html += '<h4>' + task.title + '</h4>';
                        html += '<p>' + task.description + '</p>';
                        html += '<span class="priority ' + task.priority + '">' + task.priority + '</span>';
                        html += '</div>';
                    });
                    $('#tasks-list').html(html);
                }
            }
        });
    }

    $('#create-task').on('click', function() {
        const title = $('#task-title').val().trim();
        const description = $('#task-description').val().trim();
        const priority = $('#task-priority').val();

        if (!title || !description) return;

        $.ajax({
            url: onlymatt_ajax.ajax_url,
            type: 'POST',
            data: {
                action: 'onlymatt_create_task',
                title: title,
                description: description,
                priority: priority,
                nonce: onlymatt_ajax.nonce
            },
            success: function(response) {
                if (response.success) {
                    loadTasks();
                    $('#task-title, #task-description').val('');
                } else {
                    alert('Erreur: ' + response.data);
                }
            }
        });
    });

    // Load tasks on page load
    if ($('#tasks-list').length) {
        loadTasks();
    }

    // Settings
    $('#settings-form').on('submit', function(e) {
        e.preventDefault();
        console.log('Settings form submitted');

        const settings = {
            api_base: $('#api-base').val(),
            admin_key: $('#admin-key').val(),
            max_memory: $('#max-memory').val(),
            enable_logging: $('#enable-logging').is(':checked'),
            enable_widget: $('#enable-widget').is(':checked')
        };

        console.log('Settings data:', settings);

        // Afficher le message de débogage
        $('#settings-debug').show();
        $('#debug-message').text('Sauvegarde en cours...');

        $.ajax({
            url: onlymatt_ajax.ajax_url,
            type: 'POST',
            data: {
                action: 'onlymatt_save_settings',
                settings: JSON.stringify(settings),
                nonce: onlymatt_ajax.nonce
            },
            success: function(response) {
                console.log('AJAX success:', response);
                if (response.success) {
                    $('#debug-message').text('✅ Paramètres sauvegardés avec succès !');
                    setTimeout(function() {
                        $('#settings-debug').fadeOut();
                    }, 3000);
                    alert('Paramètres sauvegardés avec succès !');
                    // Recharger la page pour voir les changements
                    location.reload();
                } else {
                    $('#debug-message').text('❌ Erreur: ' + (response.data || 'Erreur inconnue'));
                    alert('Erreur lors de la sauvegarde: ' + (response.data || 'Erreur inconnue'));
                }
            },
            error: function(xhr, status, error) {
                console.log('AJAX error:', xhr, status, error);
                $('#debug-message').text('❌ Erreur AJAX: ' + error);
                alert('Erreur AJAX: ' + error + '\nStatus: ' + xhr.status + '\nResponse: ' + xhr.responseText);
            }
        });
    });

    // Test de connexion API
    $('#test-connection').on('click', function() {
        const apiBase = $('#api-base').val().trim();
        const adminKey = $('#admin-key').val().trim();

        if (!apiBase) {
            alert('Veuillez saisir l\'URL de base de l\'API');
            return;
        }

        $('#settings-debug').show();
        $('#debug-message').text('Test de connexion en cours...');

        // Tester l'endpoint de santé
        $.ajax({
            url: apiBase + '/health',
            type: 'GET',
            timeout: 10000,
            success: function(response) {
                console.log('Health check success:', response);
                $('#debug-message').text('✅ Connexion API réussie ! Modèle: ' + (response.model || 'inconnu'));
                setTimeout(function() {
                    $('#settings-debug').fadeOut();
                }, 5000);
            },
            error: function(xhr, status, error) {
                console.log('Health check error:', xhr, status, error);
                $('#debug-message').text('❌ Échec de connexion API: ' + error + ' (Status: ' + xhr.status + ')');
            }
        });
    });
});