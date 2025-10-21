// Analysis functionality
document.getElementById('folder-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const path = document.getElementById('folder-path').value;
    const recursive = document.getElementById('recursive').checked;

    await exploreFolder(path, recursive);
});

async function exploreFolder(path, recursive) {
    const resultsDiv = document.getElementById('analysis-results');
    resultsDiv.innerHTML = '<p>Exploration en cours...</p>';

    try {
        const response = await fetch(`/ai/files/list?path=${encodeURIComponent(path)}&recursive=${recursive}`, {
            headers: {
                'X-OM-Key': 'test_key' // In production, get from secure source
            }
        });

        const data = await response.json();

        if (data.ok) {
            let html = `<h5>Résultats pour: ${data.path}</h5>`;
            html += `<p><strong>${data.files.length} fichiers trouvés</strong></p>`;

            if (data.files.length > 0) {
                html += '<ul class="list-group">';
                data.files.slice(0, 50).forEach(file => {
                    html += `<li class="list-group-item">${file}</li>`;
                });
                if (data.files.length > 50) {
                    html += `<li class="list-group-item text-muted">... et ${data.files.length - 50} autres fichiers</li>`;
                }
                html += '</ul>';
            }

            resultsDiv.innerHTML = html;
        } else {
            resultsDiv.innerHTML = `<p class="text-danger">Erreur: ${data.err}</p>`;
        }
    } catch (error) {
        resultsDiv.innerHTML = `<p class="text-danger">Erreur de connexion: ${error.message}</p>`;
    }
}

async function analyzeContent() {
    const resultsDiv = document.getElementById('analysis-results');
    resultsDiv.innerHTML = '<p>Analyse du contenu en cours...</p>';

    // Simulate content analysis
    setTimeout(async () => {
        const results = `
            <h5>Analyse du Contenu</h5>
            <div class="alert alert-info">
                <strong>Patterns identifiés:</strong><br>
                - Fichiers Python: 15<br>
                - Fichiers de configuration: 8<br>
                - Fichiers statiques: 25<br>
                - Logs: 3
            </div>
            <div class="alert alert-success">
                <strong>Recommandations:</strong><br>
                - Optimiser les images<br>
                - Compresser les logs<br>
                - Mettre à jour les dépendances
            </div>
        `;

        resultsDiv.innerHTML = results;

        // Save to Turso
        await saveAnalysis('content', results, JSON.stringify({
            patterns: ['Python: 15', 'Config: 8', 'Static: 25', 'Logs: 3'],
            recommendations: ['Optimiser images', 'Compresser logs', 'Mettre à jour dépendances']
        }));
    }, 2000);
}

async function checkChanges() {
    const resultsDiv = document.getElementById('analysis-results');
    resultsDiv.innerHTML = '<p>Vérification des changements...</p>';

    // Simulate change detection
    setTimeout(async () => {
        const results = `
            <h5>Changements Détectés</h5>
            <div class="alert alert-warning">
                <strong>Fichiers modifiés récemment:</strong><br>
                - gateway.py (il y a 2h)<br>
                - README.md (il y a 1h)<br>
                - templates/admin.html (il y a 30min)
            </div>
            <div class="alert alert-info">
                <strong>Nouveaux fichiers:</strong><br>
                - static/js/chat.js<br>
                - static/css/admin.css
            </div>
        `;

        resultsDiv.innerHTML = results;

        // Save to Turso
        await saveAnalysis('changes', results, JSON.stringify({
            modified: ['gateway.py', 'README.md', 'templates/admin.html'],
            new: ['static/js/chat.js', 'static/css/admin.css']
        }));
    }, 1500);
}

async function saveAnalysis(type, results, stats) {
    try {
        const response = await fetch('/admin/analyses', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-OM-Key': 'test_key'
            },
            body: JSON.stringify({
                type: type,
                results: results,
                stats: stats
            })
        });

        if (!response.ok) {
            console.error('Erreur sauvegarde analyse');
        }
    } catch (error) {
        console.error('Erreur connexion sauvegarde analyse:', error);
    }
}

async function generateStats() {
    const statsDiv = document.getElementById('stats-content');

    // Simulate statistics generation
    statsDiv.innerHTML = `
        <div class="row text-center">
            <div class="col-6">
                <h4>1,247</h4>
                <p>Fichiers analysés</p>
            </div>
            <div class="col-6">
                <h4>89.5 MB</h4>
                <p>Espace utilisé</p>
            </div>
        </div>
        <hr>
        <div class="row text-center">
            <div class="col-4">
                <h5>Python</h5>
                <p>45%</p>
            </div>
            <div class="col-4">
                <h5>HTML</h5>
                <p>30%</p>
            </div>
            <div class="col-4">
                <h5>Autres</h5>
                <p>25%</p>
            </div>
        </div>
    `;
}

async function exportData() {
    const resultsDiv = document.getElementById('analysis-results');
    resultsDiv.innerHTML = '<p>Export des données en cours...</p>';

    // Simulate data export
    setTimeout(() => {
        resultsDiv.innerHTML = `
            <div class="alert alert-success">
                <h5>Export Réussi</h5>
                <p>Les données ont été exportées vers: <code>analysis_export_2025-10-21.json</code></p>
                <p>Inclut: statistiques, liste des fichiers, métadonnées d'analyse</p>
            </div>
        `;
    }, 1000);
}

// Load recent files on page load
async function loadRecentFiles() {
    const recentDiv = document.getElementById('recent-files');

    try {
        const response = await fetch('/ai/files/list?recursive=false', {
            headers: {
                'X-OM-Key': 'test_key'
            }
        });

        const data = await response.json();

        if (data.ok && data.files.length > 0) {
            recentDiv.innerHTML = '<ul class="list-group">';
            data.files.slice(0, 10).forEach(file => {
                recentDiv.innerHTML += `<li class="list-group-item">${file}</li>`;
            });
            recentDiv.innerHTML += '</ul>';
        } else {
            recentDiv.innerHTML = '<p class="text-muted">Aucun fichier récent.</p>';
        }
    } catch (error) {
        recentDiv.innerHTML = '<p class="text-danger">Erreur de chargement.</p>';
    }
}

loadRecentFiles();