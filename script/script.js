// Structure de données pour stocker les objets et les tags
let files = [];
let tags = {};
let currentFile = null;

// Génération d'ID unique selon les spécifications
function generateId(type) {
    const typePrefixes = {
        'image': '1',
        'video': '2',
        'document': '3',
        'audio': '4',
        'lien': '5',
        'autre': '6'
    };
    
    const prefix = typePrefixes[type] || '0';
    const suffix = Math.floor(1000000000000000 + Math.random() * 9000000000000000);
    
    return prefix + suffix;
}

// Déterminer si un emplacement est interne ou externe
function determineLocationType(location) {
    return location.startsWith('http://') || location.startsWith('https://') ? 'externe' : 'interne';
}

// Obtenir l'icône appropriée pour le type de fichier
function getFileIcon(type) {
    const icons = {
        'image': '🖼️',
        'video': '🎬',
        'document': '📄',
        'audio': '🎵',
        'lien': '🔗',
        'autre': '📁'
    };
    return icons[type] || '📁';
}

// Vérifier si la prévisualisation est activée
function isPreviewEnabled() {
    return document.getElementById('previewCheckbox').checked;
}

// Ajout d'un fichier
document.getElementById('addFileForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const name = document.getElementById('fileName').value;
    const description = document.getElementById('fileDesc').value;
    const type = document.getElementById('fileType').value;
    const location = document.getElementById('fileLocation').value;
    const tagsInput = document.getElementById('fileTags').value;
    const locationType = determineLocationType(location);
    
    // Création de l'objet fichier
    const id = generateId(type);
    const file = {
        id,
        name,
        description,
        type,
        location,
        locationType,
        views: 0,
        createdAt: new Date().toISOString()
    };
    
    files.push(file);
    
    // Gestion des tags
    if (tagsInput) {
        const tagList = tagsInput.split(',').map(tag => tag.trim());
        
        tagList.forEach(tagName => {
            if (!tags[tagName]) {
                tags[tagName] = [];
            }
            tags[tagName].push(id);
        });
    }
    
    // Réinitialisation du formulaire
    document.getElementById('addFileForm').reset();
    
    // Mise à jour de l'affichage
    updateTagsCloud();
    performSearch();
    
    alert('Fichier ajouté avec succès! ID: ' + id);
});

// Mise à jour du nuage de tags
function updateTagsCloud() {
    const tagsCloud = document.getElementById('tagsCloud');
    tagsCloud.innerHTML = '';
    
    // Trier les tags par popularité (nombre de fichiers associés)
    const sortedTags = Object.entries(tags).sort((a, b) => b[1].length - a[1].length);
    
    // Afficher les 15 tags les plus populaires
    sortedTags.slice(0, 15).forEach(([tagName, fileIds]) => {
        const tagElement = document.createElement('div');
        tagElement.className = 'tag';
        tagElement.textContent = `#${tagName} (${fileIds.length})`;
        tagElement.addEventListener('click', () => {
            document.getElementById('searchInput').value = `#${tagName}`;
            performSearch();
        });
        tagsCloud.appendChild(tagElement);
    });
}

// Fonction de recherche
function performSearch() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    const resultsContainer = document.getElementById('resultsContainer');
    const resultsCount = document.getElementById('resultsCount');
    const sortOption = document.getElementById('sortSelect').value;
    
    // Si la recherche est vide, afficher tous les fichiers
    if (!query) {
        displayFiles(sortFiles(files, sortOption));
        resultsCount.textContent = `(${files.length} résultats)`;
        return;
    }
    
    // Logique de recherche simplifiée pour la démonstration
    const searchTerms = query.split(' ');
    let results = [];
    
    // Recherche basique par nom et tags
    files.forEach(file => {
        let match = false;
        
        // Vérification du nom
        if (file.name.toLowerCase().includes(query)) {
            match = true;
        }
        
        // Vérification des tags
        for (const [tagName, fileIds] of Object.entries(tags)) {
            if (tagName.toLowerCase().includes(query.replace('#', '')) && fileIds.includes(file.id)) {
                match = true;
            }
        }
        
        if (match) {
            results.push(file);
        }
    });
    
    displayFiles(sortFiles(results, sortOption));
    resultsCount.textContent = `(${results.length} résultats)`;
}

// Trier les fichiers selon l'option sélectionnée
function sortFiles(filesArray, sortOption) {
    switch(sortOption) {
        case 'newest':
            return [...filesArray].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
        case 'oldest':
            return [...filesArray].sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
        case 'popular':
            return [...filesArray].sort((a, b) => b.views - a.views);
        case 'name':
            return [...filesArray].sort((a, b) => a.name.localeCompare(b.name));
        default:
            return filesArray;
    }
}

// Affichage des fichiers
function displayFiles(filesToDisplay) {
    const resultsContainer = document.getElementById('resultsContainer');
    resultsContainer.innerHTML = '';
    
    if (filesToDisplay.length === 0) {
        resultsContainer.innerHTML = '<p>Aucun fichier trouvé.</p>';
        return;
    }
    
    const previewEnabled = isPreviewEnabled();
    
    filesToDisplay.forEach(file => {
        const fileCard = document.createElement('div');
        fileCard.className = 'file-card';
        fileCard.setAttribute('data-id', file.id);
        
        // Icône selon le type de fichier
        const icon = getFileIcon(file.type);
        
        // Trouver les tags associés à ce fichier
        const fileTags = [];
        for (const [tagName, fileIds] of Object.entries(tags)) {
            if (fileIds.includes(file.id)) {
                fileTags.push(tagName);
            }
        }
        
        // Prévisualisation selon le type de fichier
        let previewContent = icon;
        if (previewEnabled) {
            if (file.type === 'image') {
                previewContent = `<img src="${file.location}" alt="${file.name}" loading="lazy">`;
            } else if (file.type === 'video') {
                previewContent = `<video muted loop><source src="${file.location}" type="video/mp4">Votre navigateur ne supporte pas la lecture de vidéos.</video>`;
            }
        }
        
        fileCard.innerHTML = `
            <div class="file-preview">
                ${previewContent}
                <span class="file-type-badge">${file.type}</span>
                <span class="file-location-badge">${file.locationType}</span>
                <span class="file-views"><i class="fas fa-eye"></i> ${file.views}</span>
            </div>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-desc">${file.description}</div>
                <div class="file-tags">
                    ${fileTags.map(tag => `<span class="file-tag">#${tag}</span>`).join('')}
                </div>
            </div>
        `;
        
        // Ajouter l'événement de clic pour visualiser le fichier
        fileCard.addEventListener('click', () => {
            viewFile(file);
        });
        
        resultsContainer.appendChild(fileCard);
    });
    
    // Démarrer la lecture des vidéos si la prévisualisation est activée
    if (previewEnabled) {
        startVideoPreviews();
    }
}

// Démarrer la lecture des prévisualisations vidéo
function startVideoPreviews() {
    const videos = document.querySelectorAll('.file-preview video');
    videos.forEach(video => {
        // Démarrer la lecture en mode silencieux et en boucle
        video.play().catch(error => {
            console.log("La lecture automatique de la vidéo a été bloquée:", error);
        });
    });
}

// Arrêter la lecture des prévisualisations vidéo
function stopVideoPreviews() {
    const videos = document.querySelectorAll('.file-preview video');
    videos.forEach(video => {
        video.pause();
        video.currentTime = 0;
    });
}

// Visualiser un fichier
function viewFile(file) {
    currentFile = file;
    const modal = document.getElementById('fileModal');
    const modalTitle = document.getElementById('modalTitle');
    const fileViewer = document.getElementById('fileViewer');
    
    // Arrêter les prévisualisations vidéo
    stopVideoPreviews();
    
    // Incrémenter le compteur de vues
    file.views++;
    
    modalTitle.textContent = `Visualisation: ${file.name} (${file.views} vues)`;
    
    // Afficher le contenu en fonction du type de fichier
    if (file.type === 'image') {
        fileViewer.innerHTML = `<img src="${file.location}" alt="${file.name}">`;
    } else if (file.type === 'video') {
        fileViewer.innerHTML = `
            <video controls autoplay>
                <source src="${file.location}" type="video/mp4">
                Votre navigateur ne supporte pas la lecture de vidéos.
            </video>
        `;
    } else if (file.type === 'lien') {
        fileViewer.innerHTML = `<iframe src="${file.location}" title="${file.name}"></iframe>`;
    } else if (file.type === 'document') {
        // Pour les démonstrations, on utilise Google Docs viewer
        fileViewer.innerHTML = `<iframe src="https://docs.google.com/gview?url=${encodeURIComponent(file.location)}&embedded=true" title="${file.name}"></iframe>`;
    } else {
        fileViewer.innerHTML = `
            <div class="unsupported-format">
                <i class="fas fa-file" style="font-size: 48px; margin-bottom: 15px;"></i>
                <p>Visualisation non disponible pour ce type de fichier</p>
                <p>Emplacement: ${file.location}</p>
            </div>
        `;
    }
    
    modal.style.display = 'flex';
    
    // Mettre à jour l'affichage pour refléter le nouveau compteur de vues
    performSearch();
}

// Afficher les statistiques
function showStats() {
    const statsModal = document.getElementById('statsModal');
    const totalFiles = document.getElementById('totalFiles');
    const totalTags = document.getElementById('totalTags');
    const totalViews = document.getElementById('totalViews');
    const popularFiles = document.getElementById('popularFiles');
    
    // Calculer les statistiques
    totalFiles.textContent = files.length;
    totalTags.textContent = Object.keys(tags).length;
    
    const viewsCount = files.reduce((total, file) => total + file.views, 0);
    totalViews.textContent = viewsCount;
    
    // Afficher les fichiers les plus populaires
    popularFiles.innerHTML = '';
    const sortedFiles = [...files].sort((a, b) => b.views - a.views).slice(0, 5);
    
    if (sortedFiles.length === 0) {
        popularFiles.innerHTML = '<p>Aucun fichier avec des vues.</p>';
    } else {
        sortedFiles.forEach(file => {
            const fileElement = document.createElement('div');
            fileElement.className = 'popular-file';
            fileElement.innerHTML = `
                <div class="popular-file-info">
                    <strong>${file.name}</strong> (${file.type})
                </div>
                <div class="popular-file-views">
                    <i class="fas fa-eye"></i> ${file.views} vues
                </div>
            `;
            popularFiles.appendChild(fileElement);
        });
    }
    
    statsModal.style.display = 'flex';
}

// Sauvegarder les données dans un fichier
function saveData() {
    const data = {
        files,
        tags
    };
    
    const dataStr = JSON.stringify(data, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = 'fichiers-data.json';
    link.click();
}

// Charger les données depuis un fichier
function loadData() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    
    input.onchange = e => {
        const file = e.target.files[0];
        const reader = new FileReader();
        
        reader.onload = function(e) {
            try {
                const data = JSON.parse(e.target.result);
                
                if (data.files && data.tags) {
                    files = data.files;
                    tags = data.tags;
                    
                    updateTagsCloud();
                    performSearch();
                    
                    alert('Données chargées avec succès!');
                } else {
                    alert('Format de fichier invalide.');
                }
            } catch (error) {
                alert('Erreur lors du chargement du fichier: ' + error.message);
            }
        };
        
        reader.readAsText(file);
    };
    
    input.click();
}

// Initialisation avec quelques exemples de données
function initSampleData() {
    // Ajout de quelques fichiers exemple
    const sampleFiles = [
        {
            id: generateId('image'),
            name: 'Vacances à la montagne',
            description: 'Photos des vacances d\'hiver à la montagne',
            type: 'image',
            location: 'https://picsum.photos/600/400?random=1',
            locationType: 'externe',
            views: 15,
            createdAt: '2023-01-15T10:30:00Z'
        },
        {
            id: generateId('video'),
            name: 'Weekend à la plage',
            description: 'Vidéo de notre weekend à la plage',
            type: 'video',
            location: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
            locationType: 'externe',
            views: 8,
            createdAt: '2023-02-20T14:45:00Z'
        },
        {
            id: generateId('document'),
            name: 'Rapport de travail',
            description: 'Rapport trimestriel de travail',
            type: 'document',
            location: '/documents/rapport.pdf',
            locationType: 'interne',
            views: 23,
            createdAt: '2023-03-10T09:15:00Z'
        },
        {
            id: generateId('lien'),
            name: 'Site de voyage',
            description: 'Meilleures destinations de voyage',
            type: 'lien',
            location: 'https://www.example.com',
            locationType: 'externe',
            views: 12,
            createdAt: '2023-04-05T16:20:00Z'
        },
        {
            id: generateId('image'),
            name: 'Coucher de soleil',
            description: 'Magnifique coucher de soleil en bord de mer',
            type: 'image',
            location: 'https://picsum.photos/600/400?random=2',
            locationType: 'externe',
            views: 31,
            createdAt: '2023-05-12T18:30:00Z'
        },
        {
            id: generateId('video'),
            name: 'Randonnée en forêt',
            description: 'Vidéo de notre randonnée en forêt',
            type: 'video',
            location: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4',
            locationType: 'externe',
            views: 19,
            createdAt: '2023-06-18T11:20:00Z'
        }
    ];
    
    files = [...sampleFiles];
    
    // Ajout de tags exemple
    tags['vacances'] = [sampleFiles[0].id, sampleFiles[1].id, sampleFiles[4].id, sampleFiles[5].id];
    tags['montagne'] = [sampleFiles[0].id, sampleFiles[5].id];
    tags['plage'] = [sampleFiles[1].id, sampleFiles[4].id];
    tags['travail'] = [sampleFiles[2].id];
    tags['2023'] = [sampleFiles[0].id, sampleFiles[1].id, sampleFiles[2].id, sampleFiles[3].id, sampleFiles[4].id, sampleFiles[5].id];
    tags['web'] = [sampleFiles[3].id];
    tags['loisirs'] = [sampleFiles[0].id, sampleFiles[1].id, sampleFiles[4].id, sampleFiles[5].id];
    tags['nature'] = [sampleFiles[0].id, sampleFiles[4].id, sampleFiles[5].id];
    
    // Affichage initial
    updateTagsCloud();
    displayFiles(files);
    document.getElementById('resultsCount').textContent = `(${files.length} résultats)`;
}

// Événements
document.getElementById('searchBtn').addEventListener('click', performSearch);
document.getElementById('searchInput').addEventListener('keyup', function(e) {
    if (e.key === 'Enter') {
        performSearch();
    }
});

document.getElementById('sortSelect').addEventListener('change', performSearch);

// Case à cocher pour la prévisualisation
document.getElementById('previewCheckbox').addEventListener('change', function() {
    performSearch();
});

// Clic sur un tag dans le nuage de tags
document.getElementById('tagsCloud').addEventListener('click', function(e) {
    if (e.target.classList.contains('tag')) {
        const tagText = e.target.textContent.split(' ')[0]; // Prendre seulement le nom du tag
        document.getElementById('searchInput').value = tagText;
        performSearch();
    }
});

// Fermer le modal
document.getElementById('closeModal').addEventListener('click', function() {
    document.getElementById('fileModal').style.display = 'none';
});

document.getElementById('closeViewer').addEventListener('click', function() {
    document.getElementById('fileModal').style.display = 'none';
});

// Ouvrir dans un nouvel onglet
document.getElementById('openExternal').addEventListener('click', function() {
    if (currentFile) {
        window.open(currentFile.location, '_blank');
    }
});

// Fermer le modal en cliquant à l'extérieur
window.addEventListener('click', function(e) {
    const modal = document.getElementById('fileModal');
    if (e.target === modal) {
        modal.style.display = 'none';
    }
    
    const statsModal = document.getElementById('statsModal');
    if (e.target === statsModal) {
        statsModal.style.display = 'none';
    }
});

// Afficher les statistiques
document.getElementById('viewStatsBtn').addEventListener('click', showStats);

// Fermer le modal des statistiques
document.getElementById('closeStatsModal').addEventListener('click', function() {
    document.getElementById('statsModal').style.display = 'none';
});

// Sauvegarder les données
document.getElementById('saveDataBtn').addEventListener('click', saveData);

// Charger les données
document.getElementById('loadDataBtn').addEventListener('click', loadData);

// Initialisation
initSampleData();