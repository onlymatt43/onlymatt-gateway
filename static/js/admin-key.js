(function() {
    const STORAGE_KEY = 'om_admin_key';
    const PROMPT_MESSAGE = "Entrez la clé administrateur (X-OM-Key) pour accéder aux routes protégées.";

    function promptForKey(message) {
        const input = window.prompt(message || PROMPT_MESSAGE, '');
        if (!input) {
            return '';
        }
        const trimmed = input.trim();
        if (trimmed) {
            localStorage.setItem(STORAGE_KEY, trimmed);
        }
        return trimmed;
    }

    function currentKey() {
        return localStorage.getItem(STORAGE_KEY) || '';
    }

    window.omGetAdminKey = function(options) {
        options = options || {};
        let key = currentKey();
        if (!key && options.prompt !== false) {
            key = promptForKey(options.message);
        }
        if (!key && options.required) {
            const warn = options.requiredMessage || 'Cette action nécessite une clé administrateur.';
            window.alert(warn);
        }
        return key;
    };

    window.omAdminHeaders = function(extraHeaders) {
        let key = currentKey();
        if (!key) {
            key = promptForKey();
        }
        if (!key) {
            const error = new Error('missing_admin_key');
            error.code = 'missing_admin_key';
            throw error;
        }
        return Object.assign({}, extraHeaders || {}, { 'X-OM-Key': key });
    };

    window.omSetAdminKey = function(key) {
        if (typeof key === 'string') {
            const trimmed = key.trim();
            if (trimmed) {
                localStorage.setItem(STORAGE_KEY, trimmed);
            }
        }
    };

    window.omClearAdminKey = function() {
        localStorage.removeItem(STORAGE_KEY);
    };

    window.omPromptAdminKey = function(message) {
        const key = promptForKey(message);
        if (!key) {
            window.alert('Aucune clé administrateur fournie. Certaines fonctionnalités resteront verrouillées.');
        }
        return key;
    };
})();
