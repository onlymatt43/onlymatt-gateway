<div class="wrap onlymatt-admin-wrap">
    <h1>ONLYMATT AI - Paramètres</h1>

    <div id="settings-debug" style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; margin-bottom: 20px; display: none;">
        <strong>Débogage:</strong> <span id="debug-message"></span>
    </div>

    <form id="settings-form">
        <div class="settings-section">
            <h3>Configuration API</h3>
            <table class="form-table">
                <tr>
                    <th scope="row">URL de Base API</th>
                    <td>
                        <input type="text" id="api-base" value="<?php echo esc_attr(get_option('onlymatt_api_base', 'https://onlymatt-gateway.onrender.com')); ?>" class="regular-text" />
                        <p class="description">URL de l'API gateway ONLYMATT</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row">Clé Admin</th>
                    <td>
                        <input type="text" id="admin-key" value="<?php echo esc_attr(get_option('onlymatt_admin_key', '64b29ac4e96c12e23c1a58f93ad1509e')); ?>" class="regular-text" />
                        <p class="description">Clé d'authentification pour l'API admin</p>
                    </td>
                </tr>
            </table>
        </div>

        <div class="settings-section">
            <h3>Paramètres Mémoire</h3>
            <table class="form-table">
                <tr>
                    <th scope="row">Mémoire Maximale</th>
                    <td>
                        <input type="number" id="max-memory" value="<?php echo esc_attr(get_option('onlymatt_max_memory', 100)); ?>" min="10" max="1000" />
                        <p class="description">Nombre maximum d'éléments en mémoire (10-1000)</p>
                    </td>
                </tr>
            </table>
        </div>

        <div class="settings-section">
            <h3>Options Avancées</h3>
            <table class="form-table">
                <tr>
                    <th scope="row">Activer les Logs</th>
                    <td>
                        <label>
                            <input type="checkbox" id="enable-logging" <?php checked(get_option('onlymatt_enable_logging'), '1'); ?> />
                            Enregistrer les interactions pour le débogage
                        </label>
                    </td>
                </tr>
                <tr>
                    <th scope="row">Activer le Widget</th>
                    <td>
                        <label>
                            <input type="checkbox" id="enable-widget" <?php checked(get_option('onlymatt_enable_widget'), '1'); ?> />
                            Afficher le widget de chat sur le frontend
                        </label>
                    </td>
                </tr>
            </table>
        </div>

        <p>
            <input type="submit" value="Sauvegarder les Paramètres" class="button button-primary" />
            <button type="button" id="test-connection" class="button">Tester la Connexion API</button>
        </p>
    </form>
</div>