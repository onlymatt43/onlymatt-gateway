// Reports functionality
async function generateReport(type) {
    const reportDiv = document.getElementById('current-report');
    reportDiv.innerHTML = '<p>Génération du rapport en cours...</p>';

    try {
        let reportContent = '';

        switch(type) {
            case 'daily':
                reportContent = await generateDailyReport();
                break;
            case 'folder':
                reportContent = await generateFolderReport();
                break;
            case 'activity':
                reportContent = await generateActivityReport();
                break;
            case 'summary':
                reportContent = await generateSummaryReport();
                break;
            default:
                reportContent = 'Type de rapport inconnu';
        }

        reportDiv.innerHTML = `<pre>${reportContent}</pre>`;
        saveReport(type, reportContent);
    } catch (error) {
        reportDiv.innerHTML = `<p class="text-danger">Erreur: ${error.message}</p>`;
    }
}

async function generateDailyReport() {
    // Simulate report generation
    return `RAPPORT QUOTIDIEN - ${new Date().toLocaleDateString()}

Statistiques:
- Requêtes API: 150
- Utilisateurs actifs: 5
- Mémoires ajoutées: 3
- Tâches complétées: 2

Activité récente:
- Surveillance des dossiers: OK
- Analyse de contenu: En cours
- Génération de rapports: Complète

Recommandations:
- Vérifier les logs d'erreur
- Optimiser les performances
- Mettre à jour les prompts`;
}

async function generateFolderReport() {
    try {
        const response = await fetch('/ai/files/list?recursive=true', {
            headers: {
                'X-OM-Key': 'test_key' // In production, get from secure source
            }
        });
        const data = await response.json();

        if (data.ok) {
            return `RAPPORT DOSSIERS

Chemin analysé: ${data.path}
Nombre de fichiers: ${data.files.length}

Fichiers trouvés:
${data.files.slice(0, 20).map(f => `- ${f}`).join('\n')}

${data.files.length > 20 ? `... et ${data.files.length - 20} autres fichiers` : ''}`;
        } else {
            return `Erreur lors de l'analyse des dossiers: ${data.err}`;
        }
    } catch (error) {
        return `Erreur de connexion: ${error.message}`;
    }
}

async function generateActivityReport() {
    return `RAPPORT ACTIVITÉ

Période: Dernières 24h

Métriques:
- Sessions utilisateur: 12
- Messages chat: 45
- Analyses effectuées: 8
- Rapports générés: 3

Tendances:
- Augmentation de 15% des interactions
- Pic d'activité: 14h-16h
- Principales fonctionnalités utilisées: Chat, Analyse`;
}

async function generateSummaryReport() {
    return `RÉSUMÉ SYSTÈME

État général: ✅ Opérationnel

Composants:
- API Gateway: ✅
- Base de données Turso: ✅
- Interface Admin: ✅
- Surveillance dossiers: ✅

Performance:
- Temps de réponse moyen: 250ms
- Taux de succès: 98.5%
- Utilisation mémoire: 45%

Actions recommandées:
- Maintenance préventive dans 30 jours
- Mise à jour des dépendances
- Optimisation des requêtes`;
}

function saveReport(type, content) {
    const reports = JSON.parse(localStorage.getItem('admin_reports') || '[]');
    reports.unshift({
        id: Date.now(),
        type: type,
        content: content,
        created: new Date().toISOString()
    });

    // Keep only last 10 reports
    if (reports.length > 10) {
        reports.splice(10);
    }

    localStorage.setItem('admin_reports', JSON.stringify(reports));
    renderReportsList();
}

function renderReportsList() {
    const reports = JSON.parse(localStorage.getItem('admin_reports') || '[]');
    const reportsList = document.getElementById('reports-list');

    reportsList.innerHTML = '';

    if (reports.length === 0) {
        reportsList.innerHTML = '<p class="text-muted">Aucun rapport généré.</p>';
        return;
    }

    reports.forEach(report => {
        const reportDiv = document.createElement('div');
        reportDiv.className = 'border rounded p-2 mb-2';
        reportDiv.innerHTML = `
            <div class="d-flex justify-content-between">
                <strong>${report.type.toUpperCase()}</strong>
                <small class="text-muted">${new Date(report.created).toLocaleString()}</small>
            </div>
            <button class="btn btn-sm btn-outline-primary mt-1" onclick="viewReport(${report.id})">Voir</button>
        `;
        reportsList.appendChild(reportDiv);
    });
}

function viewReport(id) {
    const reports = JSON.parse(localStorage.getItem('admin_reports') || '[]');
    const report = reports.find(r => r.id === id);

    if (report) {
        document.getElementById('current-report').innerHTML = `<pre>${report.content}</pre>`;
    }
}

// Load reports on page load
renderReportsList();