// ONLYMATT AI Frontend JavaScript
jQuery(document).ready(function($) {
    // Frontend chat functionality
    $('.onlymatt-chat-form').on('submit', function(e) {
        e.preventDefault();

        const form = $(this);
        const message = form.find('input[name="message"]').val().trim();
        const container = form.closest('.onlymatt-chat-container');
        const messages = container.find('.messages');

        if (!message) return;

        // Add user message
        messages.append('<div class="message user"><span>' + message + '</span></div>');

        // Show loading
        const loading = $('<div class="message ai loading">Réflexion en cours...</div>');
        messages.append(loading);

        // Send AJAX
        $.ajax({
            url: onlymatt_ajax.ajax_url,
            type: 'POST',
            data: {
                action: 'onlymatt_chat',
                message: message,
                nonce: onlymatt_ajax.nonce
            },
            success: function(response) {
                loading.remove();
                if (response.success) {
                    const aiResponse = response.data.response || 'Réponse reçue';
                    messages.append('<div class="message ai"><span>' + aiResponse + '</span></div>');
                } else {
                    messages.append('<div class="message ai error">Erreur: ' + response.data + '</div>');
                }
                messages.scrollTop(messages[0].scrollHeight);
            },
            error: function() {
                loading.remove();
                messages.append('<div class="message ai error">Erreur de connexion</div>');
            }
        });

        form.find('input[name="message"]').val('');
    });

    // Hey Hi sphere functionality
    $('.hey-hi-sphere').on('click', function() {
        const sphere = $(this);
        const chat = sphere.find('.hey-hi-chat');

        if (chat.is(':visible')) {
            chat.hide();
        } else {
            chat.show();
            // Load site knowledge if not loaded
            if (!chat.data('loaded')) {
                loadSiteKnowledge(chat);
                chat.data('loaded', true);
            }
        }
    });

    function loadSiteKnowledge(chat) {
        const messages = chat.find('.messages');
        const greeting = 'Bonjour ! Je suis votre guide IA pour ce site. Comment puis-je vous aider à naviguer ?';

        // Get site info from localized script
        const siteInfo = onlymatt_ajax.site_info || {};

        if (siteInfo.main_pages && siteInfo.main_pages.length > 0) {
            greeting += '\n\nPages principales :\n';
            siteInfo.main_pages.forEach(function(page) {
                greeting += '- ' + page.title + ' (' + page.url + ')\n';
            });
        }

        messages.append('<div class="message ai"><span>' + greeting.replace(/\n/g, '<br>') + '</span></div>');
    }

    // Web builder functionality
    $('.web-builder-generate').on('click', function() {
        const builder = $(this).closest('.web-builder');
        const data = {
            business_name: builder.find('input[name="business_name"]').val(),
            industry: builder.find('select[name="industry"]').val(),
            description: builder.find('textarea[name="description"]').val(),
            pages: builder.find('input[name="pages"]').val().split(',').map(s => s.trim())
        };

        // Show loading
        const result = builder.find('.builder-result');
        result.html('<p>Génération en cours...</p>');

        // This would normally call the gateway API
        // For now, show a placeholder
        setTimeout(function() {
            result.html('<p>Site généré ! (Fonctionnalité complète disponible via l\'API gateway)</p>');
        }, 2000);
    });
});