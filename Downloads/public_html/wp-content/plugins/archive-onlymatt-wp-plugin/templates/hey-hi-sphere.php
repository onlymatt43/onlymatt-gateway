<style>
.hey-hi-sphere {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    width: 60px;
    height: 60px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    z-index: 99999;
    transition: all 0.3s ease;
    animation: heyHiPulse 2s ease-in-out infinite;
}

.hey-hi-sphere:hover {
    transform: scale(1.1);
    box-shadow: 0 12px 40px rgba(102, 126, 234, 0.4);
}

.hey-hi-sphere.active {
    animation: none;
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

.hey-hi-sphere::before {
    content: '👋';
    font-size: 24px;
    animation: heyHiWave 1s ease-in-out infinite;
}

@keyframes heyHiPulse {
    0%, 100% {
        transform: scale(1);
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    50% {
        transform: scale(1.05);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.4);
    }
}

@keyframes heyHiWave {
    0%, 100% { transform: rotate(0deg); }
    25% { transform: rotate(20deg); }
    75% { transform: rotate(-10deg); }
}

.hey-hi-tooltip {
    position: absolute;
    top: 80px;
    left: 50%;
    transform: translateX(-50%) translateY(-10px);
    background: white;
    color: #333;
    padding: 8px 12px;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    font-size: 12px;
    white-space: nowrap;
    opacity: 0;
    transition: all 0.3s ease;
    pointer-events: none;
    border: 1px solid #e9ecef;
}

.hey-hi-tooltip::after {
    content: '';
    position: absolute;
    top: 100%;
    right: 20px;
    width: 0;
    height: 0;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 6px solid white;
}

.hey-hi-sphere:hover .hey-hi-tooltip {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
}

.hey-hi-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
    display: none;
    justify-content: center;
    align-items: center;
    z-index: 10000;
    backdrop-filter: blur(5px);
}

.hey-hi-modal.show {
    display: flex;
}

.hey-hi-chat {
    background: white;
    border-radius: 20px;
    width: 90%;
    max-width: 400px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    overflow: hidden;
    animation: modalSlideIn 0.3s ease-out;
}

@keyframes modalSlideIn {
    from {
        opacity: 0;
        transform: scale(0.9) translateY(20px);
    }
    to {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}

.hey-hi-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    text-align: center;
    position: relative;
}

.hey-hi-header h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
}

.hey-hi-close {
    position: absolute;
    top: 15px;
    right: 15px;
    background: none;
    border: none;
    color: white;
    font-size: 20px;
    cursor: pointer;
    padding: 5px;
    border-radius: 50%;
    transition: background 0.3s ease;
}

.hey-hi-close:hover {
    background: rgba(255,255,255,0.2);
}

.hey-hi-messages {
    flex: 1;
    padding: 20px;
    overflow-y: auto;
    max-height: 300px;
    background: #f8f9fa;
}

.hey-hi-message {
    margin-bottom: 15px;
    padding: 12px 16px;
    border-radius: 18px;
    max-width: 80%;
    animation: messageSlideIn 0.3s ease-out;
}

.hey-hi-message.user {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    margin-left: auto;
    text-align: right;
}

.hey-hi-message.assistant {
    background: white;
    color: #2c3e50;
    border: 1px solid #e9ecef;
}

.hey-hi-input-area {
    padding: 20px;
    background: white;
    border-top: 1px solid #e9ecef;
    display: flex;
    gap: 10px;
}

.hey-hi-input {
    flex: 1;
    padding: 12px 16px;
    border: 2px solid #e9ecef;
    border-radius: 25px;
    outline: none;
    transition: border-color 0.3s ease;
}

.hey-hi-input:focus {
    border-color: #667eea;
}

.hey-hi-send {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 50%;
    width: 45px;
    height: 45px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
}

.hey-hi-send:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.hey-hi-typing {
    display: none;
    padding: 10px 20px;
    font-style: italic;
    color: #6c757d;
    background: #f8f9fa;
    animation: typingPulse 1.5s ease-in-out infinite;
}

.hey-hi-typing::before {
    content: '🤖';
    margin-right: 8px;
}

.hey-hi-quick-actions {
    padding: 15px 20px;
    background: #f8f9fa;
    border-top: 1px solid #e9ecef;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.hey-hi-action-btn {
    background: #e9ecef;
    color: #495057;
    border: none;
    padding: 6px 12px;
    border-radius: 15px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.hey-hi-action-btn:hover {
    background: #667eea;
    color: white;
    transform: translateY(-1px);
}

@media (max-width: 480px) {
    .hey-hi-sphere {
        top: 12px;
        left: 50%;
        transform: translateX(-50%);
        width: 50px;
        height: 50px;
    }

    .hey-hi-chat {
        width: 95%;
        margin: 10px;
        max-width: 360px;
    }
}
</style>

<div class="hey-hi-sphere" id="hey-hi-sphere">
    <div class="hey-hi-tooltip">
        Cliquez pour parler avec l'IA ! 👋
    </div>
</div>

<div class="hey-hi-modal" id="hey-hi-modal">
    <div class="hey-hi-chat">
        <div class="hey-hi-header">
            <h3>🤖 HEY HI - Votre Guide IA</h3>
            <button class="hey-hi-close" id="hey-hi-close">&times;</button>
        </div>

        <div class="hey-hi-messages" id="hey-hi-messages">
            <div class="hey-hi-message assistant">
                👋 Salut ! Je suis votre guide IA personnel. Je connais parfaitement ce site web et peux vous aider à naviguer, trouver des informations, ou répondre à vos questions.

                Que souhaitez-vous faire ?
            </div>
        </div>

        <div class="hey-hi-typing" id="hey-hi-typing">
            L'IA réfléchit...
        </div>

        <div class="hey-hi-quick-actions">
            <button class="hey-hi-action-btn" data-action="navigation">🧭 Navigation</button>
            <button class="hey-hi-action-btn" data-action="search">🔍 Recherche</button>
            <button class="hey-hi-action-btn" data-action="contact">📞 Contact</button>
            <button class="hey-hi-action-btn" data-action="help">❓ Aide</button>
        </div>

        <div class="hey-hi-input-area">
            <input type="text" class="hey-hi-input" id="hey-hi-input" placeholder="Posez votre question..." autocomplete="off">
            <button class="hey-hi-send" id="hey-hi-send">📤</button>
        </div>
    </div>
</div>

<script>
jQuery(document).ready(function($) {
    const $sphere = $('#hey-hi-sphere');
    const $modal = $('#hey-hi-modal');
    const $close = $('#hey-hi-close');
    const $messages = $('#hey-hi-messages');
    const $input = $('#hey-hi-input');
    const $send = $('#hey-hi-send');
    const $typing = $('#hey-hi-typing');
    const $quickActions = $('.hey-hi-action-btn');

    let conversationHistory = [];
    let isTyping = false;

    // Modal controls
    $sphere.on('click', function() {
        $modal.addClass('show');
        $sphere.addClass('active');
        $input.focus();

        // Welcome message with site knowledge
        if (conversationHistory.length === 0) {
            setTimeout(function() {
                addMessage(getWelcomeMessage(), 'assistant');
            }, 500);
        }
    });

    $close.on('click', function() {
        $modal.removeClass('show');
        $sphere.removeClass('active');
    });

    // Close modal when clicking outside
    $modal.on('click', function(e) {
        if (e.target === this) {
            $modal.removeClass('show');
            $sphere.removeClass('active');
        }
    });

    // Quick actions
    $quickActions.on('click', function() {
        const action = $(this).data('action');
        let message = '';

        switch(action) {
            case 'navigation':
                message = 'Pouvez-vous m\'aider à naviguer sur le site ? Quelles sont les principales sections ?';
                break;
            case 'search':
                message = 'Je cherche quelque chose de spécifique. Pouvez-vous m\'aider à trouver ?';
                break;
            case 'contact':
                message = 'Comment puis-je contacter l\'équipe ou obtenir de l\'aide ?';
                break;
            case 'help':
                message = 'J\'ai besoin d\'aide. Quelles sont les fonctionnalités disponibles ?';
                break;
        }

        $input.val(message);
        sendMessage();
    });

    // Send message
    function sendMessage() {
        if (isTyping) return;

        const message = $input.val().trim();
        if (!message) return;

        addMessage(message, 'user');
        $input.val('');
        conversationHistory.push({role: 'user', content: message});

        showTyping();
        isTyping = true;

        // Build context-aware prompt
        const contextPrompt = buildContextPrompt(message);

        $.post(onlymatt_ajax.ajax_url, {
            action: 'onlymatt_chat',
            message: contextPrompt,
            persona: 'site_guide',
            nonce: onlymatt_ajax.nonce
        })
        .done(function(response) {
            hideTyping();
            isTyping = false;

            if (response.success && response.data && response.data.response) {
                const aiResponse = response.data.response;
                addMessage(aiResponse, 'assistant');
                conversationHistory.push({role: 'assistant', content: aiResponse});
            } else {
                addMessage('❌ Désolé, je rencontre un problème technique. Veuillez réessayer.', 'assistant');
            }
        })
        .fail(function(xhr, status, error) {
            hideTyping();
            isTyping = false;

            let errorMessage = '❌ Erreur de connexion. Veuillez vérifier votre connexion internet.';
            if (xhr.status === 429) {
                errorMessage = '⏰ Trop de demandes. Veuillez patienter un moment.';
            }
            addMessage(errorMessage, 'assistant');
        });
    }

    $send.on('click', sendMessage);
    $input.on('keypress', function(e) {
        if (e.which === 13) {
            e.preventDefault();
            sendMessage();
        }
    });

    function buildContextPrompt(userMessage) {
        const siteInfo = onlymatt_ajax.site_info;

        return `CONTEXTE DU SITE WEB :
Site : ${siteInfo.site_title}
Description : ${siteInfo.site_description}
Page actuelle : ${siteInfo.current_page.title} (${siteInfo.current_page.url})

PAGES PRINCIPALES :
${siteInfo.main_pages.map(page => `- ${page.title}: ${page.excerpt}`).join('\n')}

QUESTION UTILISATEUR : ${userMessage}

INSTRUCTIONS :
- Tu es un guide IA qui connaît parfaitement ce site web
- Réponds de manière helpful et contextuelle
- Utilise les informations du site pour guider l'utilisateur
- Si l'utilisateur demande de la navigation, mentionne les pages disponibles
- Si l'utilisateur cherche quelque chose, aide-le à trouver l'information
- Réponds en français de manière naturelle et amicale
- Sois concis mais complet
- Utilise des emojis appropriés pour rendre la réponse engageante`;
    }

    function getWelcomeMessage() {
        const siteInfo = onlymatt_ajax.site_info;
        return `👋 Bienvenue sur ${siteInfo.site_title} !

Je suis votre guide IA personnel et je connais parfaitement ce site web. Je peux vous aider à :

🧭 **Naviguer** : Vous guider vers les différentes sections
🔍 **Rechercher** : Trouver des informations spécifiques
📞 **Contacter** : Vous aider à joindre l'équipe
❓ **Répondre** : À toutes vos questions sur le site

Vous êtes actuellement sur : **${siteInfo.current_page.title}**

Que puis-je faire pour vous aider ?`;
    }

    function addMessage(message, type) {
        const messageDiv = $('<div class="hey-hi-message ' + type + '">' + formatMessage(message) + '</div>');
        $messages.append(messageDiv);
        $messages.scrollTop($messages[0].scrollHeight);
    }

    function formatMessage(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }

    function showTyping() {
        $typing.show();
        $messages.scrollTop($messages[0].scrollHeight);
    }

    function hideTyping() {
        $typing.hide();
    }

    // Add persona for site guide
    if (typeof onlymatt_ajax !== 'undefined') {
        // This will be handled by the backend persona system
    }
});
</script>