<style>
.web-builder-container {
    max-width: 1200px;
    margin: 20px auto;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.web-builder-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 30px;
    border-radius: 16px;
    margin-bottom: 30px;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0,0,0,0.12);
}

.web-builder-header h1 {
    margin: 0 0 10px 0;
    font-size: 2.5em;
    font-weight: 700;
}

.web-builder-header p {
    margin: 0;
    font-size: 1.2em;
    opacity: 0.9;
}

.web-builder-workspace {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
    margin-bottom: 30px;
}

.web-builder-panel {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    overflow: hidden;
}

.web-builder-panel-header {
    background: #f8f9fa;
    padding: 20px;
    border-bottom: 1px solid #e9ecef;
    font-weight: 600;
    color: #495057;
}

.web-builder-input-panel {
    padding: 0;
}

.input-section {
    padding: 20px;
    border-bottom: 1px solid #e9ecef;
}

.input-section:last-child {
    border-bottom: none;
}

.input-section label {
    display: block;
    margin-bottom: 8px;
    font-weight: 600;
    color: #495057;
}

.input-section textarea,
.input-section input[type="text"],
.input-section input[type="url"] {
    width: 100%;
    padding: 12px;
    border: 2px solid #e9ecef;
    border-radius: 8px;
    font-size: 14px;
    transition: border-color 0.3s ease;
}

.input-section textarea:focus,
.input-section input[type="text"]:focus,
.input-section input[type="url"]:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.input-section textarea {
    min-height: 100px;
    resize: vertical;
}

.generate-btn {
    width: 100%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 15px;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
}

.generate-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
}

.generate-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
}

.web-builder-output {
    padding: 0;
}

.output-content {
    padding: 20px;
    max-height: 600px;
    overflow-y: auto;
}

.code-preview {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 15px;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 13px;
    line-height: 1.4;
    white-space: pre-wrap;
    word-wrap: break-word;
    max-height: 400px;
    overflow-y: auto;
}

.preview-actions {
    padding: 15px;
    background: #f8f9fa;
    border-top: 1px solid #e9ecef;
    display: flex;
    gap: 10px;
}

.preview-btn {
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s ease;
}

.preview-btn.primary {
    background: #28a745;
    color: white;
}

.preview-btn.secondary {
    background: #6c757d;
    color: white;
}

.preview-btn:hover {
    opacity: 0.8;
    transform: translateY(-1px);
}

.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.5);
    display: none;
    justify-content: center;
    align-items: center;
    z-index: 9999;
}

.loading-content {
    background: white;
    padding: 30px;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

.loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 15px;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
    .web-builder-workspace {
        grid-template-columns: 1fr;
    }

    .web-builder-header h1 {
        font-size: 2em;
    }
}
</style>

<div class="web-builder-container">
    <div class="web-builder-header">
        <h1>🌐 Web Builder AI</h1>
        <p>Créez des sites web complets avec l'intelligence artificielle</p>
    </div>

    <div style="text-align:center; margin-bottom:12px;">
        <label style="font-weight:600; color: #495057;">
            <input type="checkbox" id="builder-hey-hi-toggle" style="margin-right:8px;" checked>
            Afficher Hey Hi dans le Web Builder
        </label>
    </div>

    <div class="web-builder-workspace">
        <div class="web-builder-panel">
            <div class="web-builder-panel-header">
                📝 Configuration du projet
            </div>
            <div class="web-builder-input-panel">
                <div class="input-section">
                    <label for="project-title">Titre du projet *</label>
                    <input type="text" id="project-title" placeholder="Ex: Mon Site E-commerce" required>
                </div>

                <div class="input-section">
                    <label for="project-description">Description du projet *</label>
                    <textarea id="project-description" placeholder="Décrivez votre projet, ses objectifs, le public cible, etc." required></textarea>
                </div>

                <div class="input-section">
                    <label for="reference-sites">Sites de référence (URLs séparées par des virgules)</label>
                    <input type="text" id="reference-sites" placeholder="https://exemple1.com, https://exemple2.com">
                </div>

                <div class="input-section">
                    <label for="target-audience">Public cible</label>
                    <input type="text" id="target-audience" placeholder="Ex: Jeunes entrepreneurs, familles, professionnels">
                </div>

                <div class="input-section">
                    <label for="content-data">Données de contenu (optionnel)</label>
                    <textarea id="content-data" placeholder="Collez ici vos données, textes, informations à intégrer dans le site"></textarea>
                </div>

                <div class="input-section">
                    <label for="special-requirements">Exigences spéciales</label>
                    <textarea id="special-requirements" placeholder="Fonctionnalités spécifiques, style particulier, contraintes techniques, etc."></textarea>
                </div>

                <button id="generate-website" class="generate-btn">
                    🚀 Générer le site web
                </button>
            </div>
        </div>

        <div class="web-builder-panel">
            <div class="web-builder-panel-header">
                💻 Code généré
            </div>
            <div class="web-builder-output">
                <div class="output-content">
                    <div id="generated-code" class="code-preview">
                        <!-- Le code généré apparaîtra ici -->
                        <div style="text-align: center; color: #6c757d; padding: 40px;">
                            <div style="font-size: 3em; margin-bottom: 20px;">🎯</div>
                            <h3>Prêt à créer votre site web !</h3>
                            <p>Remplissez le formulaire à gauche et cliquez sur "Générer le site web"</p>
                        </div>
                    </div>
                </div>
                <div class="preview-actions">
                    <button id="copy-code" class="preview-btn primary" style="display: none;">
                        📋 Copier le code
                    </button>
                    <button id="download-html" class="preview-btn secondary" style="display: none;">
                        💾 Télécharger HTML
                    </button>
                    <button id="preview-site" class="preview-btn secondary" style="display: none;">
                        👁️ Aperçu
                    </button>
                </div>
            </div>
        </div>
    </div>
</div>

<div id="loading-overlay" class="loading-overlay">
    <div class="loading-content">
        <div class="loading-spinner"></div>
        <h3>🧠 L'IA analyse et crée votre site web...</h3>
        <p>Cette opération peut prendre quelques instants</p>
    </div>
</div>

<script>
jQuery(document).ready(function($) {
    const $generateBtn = $('#generate-website');
    const $loadingOverlay = $('#loading-overlay');
    const $generatedCode = $('#generated-code');
    const $copyCode = $('#copy-code');
    const $downloadHtml = $('#download-html');
    const $previewSite = $('#preview-site');

    $generateBtn.on('click', function() {
        const projectData = {
            title: $('#project-title').val().trim(),
            description: $('#project-description').val().trim(),
            referenceSites: $('#reference-sites').val().trim(),
            targetAudience: $('#target-audience').val().trim(),
            contentData: $('#content-data').val().trim(),
            specialRequirements: $('#special-requirements').val().trim()
        };

        if (!projectData.title || !projectData.description) {
            alert('Veuillez remplir au moins le titre et la description du projet.');
            return;
        }

        // Show loading
        $loadingOverlay.show();
        $generateBtn.prop('disabled', true).text('🔄 Génération en cours...');

        // Build the AI prompt
        const prompt = buildWebBuilderPrompt(projectData);

        // Send to AI
        $.post(onlymatt_ajax.ajax_url, {
            action: 'onlymatt_chat',
            message: prompt,
            persona: 'web_developer',
            nonce: onlymatt_ajax.nonce
        })
        .done(function(response) {
            $loadingOverlay.hide();
            $generateBtn.prop('disabled', false).text('🚀 Générer le site web');

            if (response.success && response.data && response.data.response) {
                displayGeneratedCode(response.data.response, projectData.title);
            } else {
                $generatedCode.html('<div style="color: #dc3545; padding: 20px;"><strong>❌ Erreur:</strong> ' + (response.data?.error || 'Impossible de générer le site web. Veuillez réessayer.') + '</div>');
            }
        })
        .fail(function(xhr, status, error) {
            $loadingOverlay.hide();
            $generateBtn.prop('disabled', false).text('🚀 Générer le site web');

            let errorMessage = '❌ Erreur de connexion. Veuillez vérifier votre connexion internet et réessayer.';
            if (xhr.status === 429) {
                errorMessage = '⏰ Trop de requêtes. Veuillez patienter un moment avant de réessayer.';
            }

            $generatedCode.html('<div style="color: #dc3545; padding: 20px;"><strong>Erreur:</strong> ' + errorMessage + '</div>');
        });
    });

    function buildWebBuilderPrompt(data) {
        return `CRÉATION DE SITE WEB COMPLET

DONNÉES DU PROJET :
- Titre : ${data.title}
- Description : ${data.description}
- Public cible : ${data.targetAudience || 'Non spécifié'}
- Sites de référence : ${data.referenceSites || 'Aucun'}
- Données de contenu : ${data.contentData || 'Aucune donnée fournie'}
- Exigences spéciales : ${data.specialRequirements || 'Aucune'}

INSTRUCTIONS :
1. Analyse les données fournies et les sites de référence
2. Crée un site web complet et responsive
3. Utilise les meilleures pratiques de développement web
4. Intègre le contenu fourni de manière cohérente
5. Assure-toi que le design est moderne et professionnel

FORMAT DE RÉPONSE :
1. 📊 ANALYSE DES DONNÉES ET RECHERCHE
2. 🎨 STRUCTURE ET DESIGN PROPOSÉ
3. 💻 CODE HTML/CSS/JS COMPLET
4. 📝 EXPLICATIONS TECHNIQUES

Génère UNIQUEMENT le code HTML complet avec CSS et JavaScript intégrés. Le code doit être prêt à être copié et utilisé directement.`;
    }

    function displayGeneratedCode(code, title) {
        // Clean and format the code
        const formattedCode = code.replace(/```html|```css|```javascript|```/g, '').trim();

        $generatedCode.html(`<pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word;">${escapeHtml(formattedCode)}</pre>`);

        // Show action buttons
        $copyCode.show();
        $downloadHtml.show();
        $previewSite.show();

        // Store the code for actions
        $generatedCode.data('code', formattedCode);
        $generatedCode.data('title', title);
    }

    $copyCode.on('click', function() {
        const code = $generatedCode.data('code');
        if (code) {
            navigator.clipboard.writeText(code).then(function() {
                $copyCode.text('✅ Copié !');
                setTimeout(function() {
                    $copyCode.text('📋 Copier le code');
                }, 2000);
            });
        }
    });

    $downloadHtml.on('click', function() {
        const code = $generatedCode.data('code');
        const title = $generatedCode.data('title') || 'site-web';

        if (code) {
            const blob = new Blob([code], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = title.toLowerCase().replace(/\s+/g, '-') + '.html';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    });

    $previewSite.on('click', function() {
        const code = $generatedCode.data('code');
        if (code) {
            const newWindow = window.open('', '_blank');
            newWindow.document.write(code);
            newWindow.document.close();
        }
    });

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
</script>

<!-- Hey Hi toggle behaviour (persist in localStorage) -->
<script>
jQuery(document).ready(function($) {
    const $toggle = $('#builder-hey-hi-toggle');

    function setHeyHiEnabled(enabled) {
        if (enabled) {
            $('body').addClass('hey-hi-enabled');
            localStorage.setItem('onlymatt_hey_hi_in_builder', '1');
        } else {
            $('body').removeClass('hey-hi-enabled');
            localStorage.setItem('onlymatt_hey_hi_in_builder', '0');
            // close modal if open
            $('#hey-hi-modal').removeClass('show');
            $('#hey-hi-sphere').removeClass('active');
        }
    }

    // Initialize from localStorage (default: enabled)
    try {
        const stored = localStorage.getItem('onlymatt_hey_hi_in_builder');
        const enabled = stored === null ? true : stored === '1';
        $toggle.prop('checked', enabled);
        setHeyHiEnabled(enabled);
    } catch (e) {
        // localStorage might be unavailable in some environments
        $toggle.prop('checked', true);
        setHeyHiEnabled(true);
    }

    $toggle.on('change', function() {
        setHeyHiEnabled(this.checked);
    });
});
</script>

<style>
/* Hide Hey Hi by default in the builder page unless user enables it with the toggle above */
#hey-hi-sphere, #hey-hi-modal { display: none !important; }
body.hey-hi-enabled #hey-hi-sphere { display: flex !important; }
/* Modal remains controlled by its own .show class; ensure it can appear when enabled */
body.hey-hi-enabled #hey-hi-modal.show { display: flex !important; }
</style>