<div class="wrap onlymatt-admin-wrap">
    <h1>ONLYMATT AI - Chat</h1>

    <div id="chat-container">
        <div id="chat-messages" style="border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 10px; background: #f9f9f9; margin-bottom: 10px;"></div>

        <div id="chat-inputs">
            <select id="chat-persona" style="margin-right: 10px;">
                <option value="general_assistant">Assistant Général</option>
                <option value="web_developer">Développeur Web</option>
                <option value="site_guide">Guide du Site</option>
            </select>
            <input type="text" id="chat-message" placeholder="Tapez votre message..." style="flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" />
            <button id="send-message" class="button button-primary" style="margin-left: 10px;">Envoyer</button>
        </div>
    </div>
</div>