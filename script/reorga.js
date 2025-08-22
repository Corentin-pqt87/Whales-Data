// Structure de données pour stocker les objets, tags et collections
let files = [];
let tags = {};
let collections = [];
let currentFile = null;
let currentCollectionId = null;
let isListView = false;
let isEditingFile = false;
let isEditingCollection = false;
let searchHistory = [];

// ==================== FONCTIONS D'INITIALISATION ====================
document.addEventListener('DOMContentLoaded', function() {
    loadSearchHistory();
    enhanceSearchExperience();
    // initSampleData(); // Décommentez pour charger des données d'exemple
});

// ==================== FONCTIONS UTILITAIRES ====================
// Génération d'ID unique selon les spécifications
function generateId(type) {
    const typePrefixes = {
        'image': '1',
        'video': '2',
        'document': '3',
        'audio': '4',
        'lien': '5',
        'autre': '6',
        'collection': '7'
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

// Formater la date pour l'affichage
function formatDate(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    
    if (diffMins < 1) return 'à l\'instant';
    if (diffMins < 60) return `il y a ${diffMins} min`;
    if (diffHours < 24) return `il y a ${diffHours} h`;
    
    return date.toLocaleDateString();
}

// Tronquer le texte si trop long
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// ==================== GESTION DES FICHIERS ====================
// Ajout ou modification d'un fichier
document.getElementById('addFileForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const id = document.getElementById('fileId').value;
    const name = document.getElementById('fileName').value;
    const description = document.getElementById('fileDesc').value;
    const type = document.getElementById('fileType').value;
    const location = document.getElementById('fileLocation').value;
    const tagsInput = document.getElementById('fileTags').value;
    const locationType = determineLocationType(location);
    
    // Récupérer les collections sélectionnées
    const selectedCollections = [];
    document.querySelectorAll('.collection-checkbox input:checked').forEach(checkbox => {
        selectedCollections.push(checkbox.value);
    });
    
    if (isEditingFile && id) {
        // Modification d'un fichier existant
        const fileIndex = files.findIndex(f => f.id === id);
        if (fileIndex !== -1) {
            // Retirer l'ancien fichier de ses collections
            if (files[fileIndex].collections) {
                files[fileIndex].collections.forEach(collectionId => {
                    const collection = collections.find(c => c.id === collectionId);
                    if (collection && collection.files) {
                        const fileIndexInCollection = collection.files.indexOf(id);
                        if (fileIndexInCollection !== -1) {
                            collection.files.splice(fileIndexInCollection, 1);
                        }
                    }
                });
            }
            
            // Mettre à jour le fichier
            files[fileIndex] = {
                ...files[fileIndex],
                name,
                description,
                type,
                location,
                locationType,
                collections: selectedCollections
            };
            
            // Ajouter le fichier aux nouvelles collections
            selectedCollections.forEach(collectionId => {
                const collection = collections.find(c => c.id === collectionId);
                if (collection) {
                    if (!collection.files) collection.files = [];
                    if (!collection.files.includes(id)) {
                        collection.files.push(id);
                    }
                    collection.updatedAt = new Date().toISOString();
                }
            });
            
            // Mettre à jour les tags
            updateFileTags(id, tagsInput);
            
            alert('Fichier modifié avec succès!');
        }
    } else {
        // Création d'un nouveau fichier
        const newId = generateId(type);
        const file = {
            id: newId,
            name,
            description,
            type,
            location,
            locationType,
            collections: selectedCollections,
            views: 0,
            createdAt: new Date().toISOString()
        };
        
        files.push(file);
        
        // Ajouter le fichier aux collections
        selectedCollections.forEach(collectionId => {
            const collection = collections.find(c => c.id === collectionId);
            if (collection) {
                if (!collection.files) collection.files = [];
                collection.files.push(newId);
                collection.updatedAt = new Date().toISOString();
            }
        });
        
        // Gestion des tags
        if (tagsInput) {
            const tagList = tagsInput.split(',').map(tag => tag.trim());
            
            tagList.forEach(tagName => {
                if (tagName) { // Vérifier que le tag n'est pas vide
                    if (!tags[tagName]) {
                        tags[tagName] = [];
                    }
                    if (!tags[tagName].includes(newId)) {
                        tags[tagName].push(newId);
                    }
                }
            });
        }
        
        alert('Fichier ajouté avec succès! ID: ' + newId);
    }
    
    // Réinitialisation du formulaire
    resetFileForm();
    
    // Mise à jour de l'affichage
    updateCollectionsList();
    updateTagsCloud();
    performSearch();
});

// Mettre à jour les tags d'un fichier
function updateFileTags(fileId, tagsInput) {
    // Retirer le fichier de tous les tags existants
    Object.keys(tags).forEach(tagName => {
        const index = tags[tagName].indexOf(fileId);
        if (index !== -1) {
            tags[tagName].splice(index, 1);
            // Supprimer le tag s'il ne contient plus de fichiers
            if (tags[tagName].length === 0) {
                delete tags[tagName];
            }
        }
    });
    
    // Ajouter les nouveaux tags
    if (tagsInput) {
        const tagList = tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag !== '');
        
        tagList.forEach(tagName => {
            if (!tags[tagName]) {
                tags[tagName] = [];
            }
            if (!tags[tagName].includes(fileId)) {
                tags[tagName].push(fileId);
            }
        });
    }
}

// Réinitialiser le formulaire de fichier
function resetFileForm() {
    document.getElementById('fileFormTitle').textContent = 'Ajouter un fichier';
    document.getElementById('fileId').value = '';
    document.getElementById('addFileForm').reset();
    document.getElementById('submitFileBtn').textContent = 'Ajouter le fichier';
    document.getElementById('cancelEditBtn').style.display = 'none';
    isEditingFile = false;
}

// Modifier un fichier
function editFile(file) {
    isEditingFile = true;
    document.getElementById('fileFormTitle').textContent = 'Modifier le fichier';
    document.getElementById('fileId').value = file.id;
    document.getElementById('fileName').value = file.name;
    document.getElementById('fileDesc').value = file.description || '';
    document.getElementById('fileType').value = file.type;
    document.getElementById('fileLocation').value = file.location;
    
    // Récupérer les tags du fichier
    const fileTags = [];
    for (const [tagName, fileIds] of Object.entries(tags)) {
        if (fileIds.includes(file.id)) {
            fileTags.push(tagName);
        }
    }
    document.getElementById('fileTags').value = fileTags.join(', ');
    
    // Cocher les collections du fichier
    document.querySelectorAll('.collection-checkbox input').forEach(checkbox => {
        checkbox.checked = file.collections && file.collections.includes(checkbox.value);
    });
    
    document.getElementById('submitFileBtn').textContent = 'Modifier le fichier';
    document.getElementById('cancelEditBtn').style.display = 'inline-block';
    
    // Scroll to form
    document.querySelector('.add-file-section').scrollIntoView({ behavior: 'smooth' });
}

// Annuler l'édition de fichier
document.getElementById('cancelEditBtn').addEventListener('click', resetFileForm);

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
        // Pour les documents, on utilise Google Docs viewer
        fileViewer.innerHTML = `<iframe src="https://docs.google.com/gview?url=${encodeURIComponent(file.location)}&embedded=true" style="width:100%; height:500px;" frameborder="0"></iframe>`;
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

// Modifier un fichier depuis le modal
document.getElementById('editFileBtn').addEventListener('click', function() {
    if (currentFile) {
        document.getElementById('fileModal').style.display = 'none';
        editFile(currentFile);
    }
});

// Supprimer un fichier
document.getElementById('deleteFileBtn').addEventListener('click', function() {
    if (currentFile) {
        showConfirmModal(
            'Supprimer le fichier',
            `Êtes-vous sûr de vouloir supprimer le fichier "${currentFile.name}" ? Cette action est irréversible.`,
            () => {
                // Retirer le fichier de toutes les collections
                collections.forEach(collection => {
                    if (collection.files) {
                        const index = collection.files.indexOf(currentFile.id);
                        if (index !== -1) {
                            collection.files.splice(index, 1);
                        }
                    }
                });
                
                // Retirer le fichier de tous les tags
                Object.keys(tags).forEach(tagName => {
                    const index = tags[tagName].indexOf(currentFile.id);
                    if (index !== -1) {
                        tags[tagName].splice(index, 1);
                        // Supprimer le tag s'il ne contient plus de fichiers
                        if (tags[tagName].length === 0) {
                            delete tags[tagName];
                        }
                    }
                });
                
                // Supprimer le fichier
                const fileIndex = files.findIndex(f => f.id === currentFile.id);
                if (fileIndex !== -1) {
                    files.splice(fileIndex, 1);
                }
                
                // Fermer le modal et mettre à jour l'affichage
                document.getElementById('fileModal').style.display = 'none';
                updateCollectionsList();
                updateTagsCloud();
                performSearch();
                
                alert('Fichier supprimé avec succès!');
            }
        );
    }
});

// ==================== GESTION DES COLLECTIONS ====================
// Créer ou modifier une collection
document.getElementById('collectionForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const id = document.getElementById('collectionId').value;
    const name = document.getElementById('collectionName').value;
    const description = document.getElementById('collectionDescription').value;
    const color = document.getElementById('collectionColor').value;
    
    if (isEditingCollection && id) {
        // Modification d'une collection existante
        const collectionIndex = collections.findIndex(c => c.id === id);
        if (collectionIndex !== -1) {
            collections[collectionIndex] = {
                ...collections[collectionIndex],
                name,
                description,
                color,
                updatedAt: new Date().toISOString()
            };
            alert('Collection modifiée avec succès!');
        }
    } else {
        // Création d'une nouvelle collection
        const collection = {
            id: generateId('collection'),
            name,
            description,
            color,
            files: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        };
        
        collections.push(collection);
        alert(`Collection "${name}" créée avec succès!`);
    }
    
    // Fermer le modal
    document.getElementById('collectionModal').style.display = 'none';
    document.getElementById('collectionForm').reset();
    
    // Mettre à jour les interfaces
    updateCollectionsList();
    updateCollectionsSelect();
    performSearch();
});

// Modifier une collection
function editCollection(collectionId) {
    const collection = collections.find(c => c.id === collectionId);
    if (!collection) return;
    
    isEditingCollection = true;
    document.getElementById('collectionModalTitle').textContent = 'Modifier la collection';
    document.getElementById('collectionId').value = collection.id;
    document.getElementById('collectionName').value = collection.name;
    document.getElementById('collectionDescription').value = collection.description || '';
    document.getElementById('collectionColor').value = collection.color;
    document.getElementById('saveCollectionBtn').textContent = 'Modifier la collection';
    document.getElementById('deleteCollectionBtn').style.display = 'inline-block';
    
    document.getElementById('collectionModal').style.display = 'flex';
}

// Supprimer une collection
function deleteCollection(collectionId) {
    showConfirmModal(
        'Supprimer la collection',
        'Êtes-vous sûr de vouloir supprimer cette collection ? Les fichiers ne seront pas supprimés, mais seront retirés de la collection.',
        () => {
            const collectionIndex = collections.findIndex(c => c.id === collectionId);
            if (collectionIndex !== -1) {
                // Retirer la collection de tous les fichiers
                const collection = collections[collectionIndex];
                if (collection.files) {
                    collection.files.forEach(fileId => {
                        const file = files.find(f => f.id === fileId);
                        if (file && file.collections) {
                            const collectionIndexInFile = file.collections.indexOf(collectionId);
                            if (collectionIndexInFile !== -1) {
                                file.collections.splice(collectionIndexInFile, 1);
                            }
                        }
                    });
                }
                
                // Supprimer la collection
                collections.splice(collectionIndex, 1);
                
                // Mettre à jour l'affichage
                updateCollectionsList();
                updateCollectionsSelect();
                performSearch();
                
                alert('Collection supprimée avec succès!');
            }
        }
    );
}

// Annuler l'édition de collection
document.getElementById('cancelCollectionBtn').addEventListener('click', function() {
    document.getElementById('collectionModal').style.display = 'none';
    resetCollectionForm();
});

// Réinitialiser le formulaire de collection
function resetCollectionForm() {
    document.getElementById('collectionModalTitle').textContent = 'Créer une nouvelle collection';
    document.getElementById('collectionId').value = '';
    document.getElementById('collectionForm').reset();
    document.getElementById('collectionColor').value = '#3498db';
    document.getElementById('saveCollectionBtn').textContent = 'Créer la collection';
    document.getElementById('deleteCollectionBtn').style.display = 'none';
    isEditingCollection = false;
}

// Mise à jour de la liste des collections
function updateCollectionsList() {
    const collectionsList = document.getElementById('collectionsList');
    collectionsList.innerHTML = '';
    
    if (collections.length === 0) {
        collectionsList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <p>Aucune collection</p>
                <p>Créez votre première collection pour organiser vos fichiers</p>
            </div>
        `;
        return;
    }
    
    // Trier les collections par date de modification
    const sortedCollections = [...collections].sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
    
    // Ajouter l'option "Tous les fichiers"
    const allFilesItem = document.createElement('div');
    allFilesItem.className = `collection-item ${currentCollectionId === null ? 'active' : ''}`;
    allFilesItem.innerHTML = `
        <div class="collection-info">
            <div class="collection-color" style="background-color: #3498db"></div>
            <div class="collection-name">Tous les fichiers</div>
        </div>
        <div class="collection-count">${files.length}</div>
    `;
    allFilesItem.addEventListener('click', () => {
        currentCollectionId = null;
        updateCollectionsList();
        performSearch();
    });
    collectionsList.appendChild(allFilesItem);
    
    // Ajouter les collections
    sortedCollections.forEach(collection => {
        const collectionItem = document.createElement('div');
        collectionItem.className = `collection-item ${currentCollectionId === collection.id ? 'active' : ''}`;
        collectionItem.innerHTML = `
            <div class="collection-info">
                <div class="collection-color" style="background-color: ${collection.color}"></div>
                <div class="collection-name">${collection.name}</div>
            </div>
            <div class="collection-count">${collection.files ? collection.files.length : 0}</div>
            <div class="collection-actions">
                <button class="collection-action-btn edit-collection" data-id="${collection.id}" title="Modifier">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="collection-action-btn delete-collection" data-id="${collection.id}" title="Supprimer">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        collectionItem.addEventListener('click', (e) => {
            if (!e.target.closest('.collection-actions')) {
                currentCollectionId = collection.id;
                updateCollectionsList();
                performSearch();
            }
        });
        
       // Ajouter les événements pour les boutons d'action
        const editBtn = collectionItem.querySelector('.edit-collection');
        const deleteBtn = collectionItem.querySelector('.delete-collection');
        
        editBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            editCollection(collection.id);
        });
        
        deleteBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            deleteCollection(collection.id);
        });
        
        collectionsList.appendChild(collectionItem);
    });
}

// Mise à jour de la sélection de collections dans le formulaire
function updateCollectionsSelect() {
    const collectionsSelect = document.getElementById('collectionsSelect');
    collectionsSelect.innerHTML = '';
    
    if (collections.length === 0) {
        collectionsSelect.innerHTML = '<p>Aucune collection disponible. Créez-en une d\'abord.</p>';
        return;
    }
    
    collections.forEach(collection => {
        const checkboxContainer = document.createElement('div');
        checkboxContainer.className = 'collection-checkbox';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `collection-${collection.id}`;
        checkbox.name = 'collections';
        checkbox.value = collection.id;
        
        const label = document.createElement('label');
        label.className = 'collection-checkbox-label';
        label.htmlFor = `collection-${collection.id}`;
        label.innerHTML = `
            <span class="collection-checkbox-color" style="background-color: ${collection.color}"></span>
            ${collection.name}
        `;
        
        checkboxContainer.appendChild(checkbox);
        checkboxContainer.appendChild(label);
        collectionsSelect.appendChild(checkboxContainer);
    });
}

// ==================== GESTION DES TAGS ====================
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

// ==================== RECHERCHE ET FILTRAGE ====================
// Fonction de recherche
function performSearch() {
    const query = document.getElementById('searchInput').value;
    const resultsContainer = document.getElementById('resultsContainer');
    const resultsCount = document.getElementById('resultsCount');
    const resultsTitle = document.getElementById('resultsTitle');
    const sortOption = document.getElementById('sortSelect').value;
    
    let results = [];
    
    // Déterminer les fichiers à afficher en fonction de la collection active
    if (currentCollectionId) {
        const collection = collections.find(c => c.id === currentCollectionId);
        if (collection && collection.files) {
            results = files.filter(file => collection.files.includes(file.id));
            resultsTitle.textContent = `Fichiers dans la collection "${collection.name}"`;
        }
    } else {
        results = [...files];
        resultsTitle.textContent = 'Résultats de recherche';
    }
    
    // Appliquer la recherche textuelle si spécifiée
    if (query.trim()) {
        results = filterWithAdvancedSearch(query, results);
    }
    
    displayFiles(sortFiles(results, sortOption));
    resultsCount.textContent = `(${results.length} résultat${results.length !== 1 ? 's' : ''})`;
    
    // Ajouter à l'historique après la recherche
    if (query.trim()) {
        addToSearchHistory(query);
    }
}

// Fonction pour gérer la recherche avancée avec NOT
function filterWithAdvancedSearch(query, initialResults) {
    let results = [...initialResults];
    const queryLower = query.toLowerCase();
    
    // Détecter les patterns NOT ou parenthèses
    const notPattern = /not\(([^)]+)\)/gi;
    const notPatternSimple = /not\s+([^\s)]+)/gi;
    
    let match;
    const excludeTerms = [];
    
    // Extraire les termes à exclure avec not()
    while ((match = notPattern.exec(queryLower)) !== null) {
        excludeTerms.push(match[1].trim());
    }
    
    // Extraire les termes à exclure avec not (sans parenthèses)
    while ((match = notPatternSimple.exec(queryLower)) !== null) {
        excludeTerms.push(match[1].trim());
    }
    
    // Filtrer les résultats pour exclure les termes indésirables
    if (excludeTerms.length > 0) {
        results = results.filter(file => {
            return !excludeTerms.some(excludeTerm => {
                // Vérifier si le terme exclu est un tag
                if (excludeTerm.startsWith('#')) {
                    const tagName = excludeTerm.substring(1);
                    return tags[tagName] && tags[tagName].includes(file.id);
                }
                
                // Vérifier si le terme exclu est dans le nom ou la description
                const nameMatch = file.name.toLowerCase().includes(excludeTerm);
                const descMatch = file.description && file.description.toLowerCase().includes(excludeTerm);
                
                return nameMatch || descMatch;
            });
        });
    }
    
    // Maintenant traiter les termes inclusifs (le reste de la requête)
    const inclusiveQuery = queryLower
        .replace(notPattern, '')
        .replace(notPatternSimple, '')
        .trim();
    
    if (inclusiveQuery) {
        const searchTerms = inclusiveQuery.split(/\s+/).filter(term => term.length > 0);
        
        results = results.filter(file => {
            return searchTerms.every(term => {
                // Ignorer les opérateurs vides
                if (term === 'and' || term === 'or' || term === 'not' || term === '') {
                    return true;
                }
                
                // Si le terme commence par #, c'est un tag
                if (term.startsWith('#')) {
                    const tagName = term.substring(1);
                    return tags[tagName] && tags[tagName].includes(file.id);
                }
                
                // Recherche dans le nom et la description
                const nameMatch = file.name.toLowerCase().includes(term);
                const descMatch = file.description && file.description.toLowerCase().includes(term);
                
                return nameMatch || descMatch;
            });
        });
    }
    
    return results;
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
        resultsContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <p>Aucun fichier trouvé</p>
                <p>Essayez de modifier vos critères de recherche</p>
            </div>
        `;
        return;
    }
    
    const previewEnabled = isPreviewEnabled();
    
    // Appliquer la classe pour la vue liste si nécessaire
    if (isListView) {
        resultsContainer.classList.add('list-view');
    } else {
        resultsContainer.classList.remove('list-view');
    }
    
    filesToDisplay.forEach(file => {
        const fileCard = document.createElement('div');
        fileCard.className = `file-card ${isListView ? 'list-view' : ''}`;
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
        
        // Trouver les collections associées à ce fichier
        const fileCollections = [];
        if (file.collections && file.collections.length > 0) {
            file.collections.forEach(collectionId => {
                const collection = collections.find(c => c.id === collectionId);
                if (collection) {
                    fileCollections.push(collection);
                }
            });
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
                ${fileCollections.length > 0 ? `
                    <div class="file-collections">
                        ${fileCollections.map(collection => `
                            <span class="file-collection" style="background-color: ${collection.color}20; color: ${collection.color}">
                                ${collection.name}
                            </span>
                        `).join('')}
                    </div>
                ` : ''}
                ${fileTags.length > 0 ? `
                    <div class="file-tags">
                        ${fileTags.map(tag => `<span class="file-tag">#${tag}</span>`).join('')}
                    </div>
                ` : ''}
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

// ==================== GESTION DE L'HISTORIQUE DE RECHERCHE ====================
// Ajouter une recherche à l'historique
function addToSearchHistory(query) {
    if (!query.trim()) return;
    
    const resultCount = getCurrentResultCount();
    
    // Vérifier si la recherche existe déjà
    const existingIndex = searchHistory.findIndex(item => item.query === query);
    
    if (existingIndex !== -1) {
        // Mettre à jour la recherche existante
        searchHistory[existingIndex].timestamp = new Date().toISOString();
        searchHistory[existingIndex].resultCount = resultCount;
        
        // Déplacer en première position
        const existingItem = searchHistory.splice(existingIndex, 1)[0];
        searchHistory.unshift(existingItem);
    } else {
        // Ajouter une nouvelle recherche
        searchHistory.unshift({
            query: query,
            timestamp: new Date().toISOString(),
            resultCount: resultCount
        });
        
        // Garder seulement les 5 dernières recherches
        if (searchHistory.length > 5) {
            searchHistory.pop(); // Supprimer la plus ancienne
        }
    }
    
    // Sauvegarder dans le localStorage
    localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
    
    // Mettre à jour l'affichage
    updateSearchHistory();
}

// Mettre à jour l'affichage de l'historique
function updateSearchHistory() {
    const historyList = document.getElementById('historyList');
    historyList.innerHTML = '';
    
    if (searchHistory.length === 0) {
        historyList.innerHTML = `
            <div class="empty-history">
                <i class="fas fa-clock"></i>
                <p>Aucune recherche récente</p>
            </div>
        `;
        return;
    }
    
    searchHistory.forEach((item, index) => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        
        const displayQuery = item.query.length > 45 
            ? item.query.substring(0, 42) + '...' 
            : item.query;
        
        historyItem.innerHTML = `
            <div class="history-content">
                <div class="history-query" title="${item.query.replace(/"/g, '&quot;')}">
                    ${displayQuery}
                </div>
                <div class="history-info">
                    <span class="history-date">${formatDate(item.timestamp)}</span>
                    <span class="history-results">${item.resultCount} résultat(s)</span>
                </div>
            </div>
            <button class="history-remove" data-index="${index}" title="Supprimer cette recherche">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Ajouter une classe spéciale pour les recherches avec NOT
        if (item.query.toLowerCase().includes('not')) {
            historyItem.classList.add('has-exclusion');
        }
        
        // Événement pour recharger la recherche
        historyItem.addEventListener('click', (e) => {
            if (!e.target.closest('.history-remove')) {
                document.getElementById('searchInput').value = item.query;
                performSearch();
            }
        });
        
        // Événement pour supprimer de l'historique
        historyItem.querySelector('.history-remove').addEventListener('click', (e) => {
            e.stopPropagation();
            removeFromSearchHistory(index);
        });
        
        historyList.appendChild(historyItem);
    });
}

// Charger l'historique au démarrage
function loadSearchHistory() {
    const savedHistory = localStorage.getItem('searchHistory');
    if (savedHistory) {
        try {
            searchHistory = JSON.parse(savedHistory);
            // S'assurer qu'on ne garde que 5 éléments maximum
            if (searchHistory.length > 5) {
                searchHistory = searchHistory.slice(0, 5);
            }
        } catch (e) {
            console.error('Erreur lors du chargement de l\'historique:', e);
            searchHistory = [];
        }
    } else {
        // Si pas d'historique sauvegardé, initialiser avec un tableau vide
        searchHistory = [];
    }
    updateSearchHistory();
}

// Supprimer de l'historique
function removeFromSearchHistory(index) {
    searchHistory.splice(index, 1);
    localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
    updateSearchHistory();
}

// Effacer tout l'historique
function clearSearchHistory() {
    showConfirmModal(
        'Effacer l\'historique',
        'Êtes-vous sûr de vouloir effacer tout l\'historique des recherches ?',
        () => {
            searchHistory = [];
            localStorage.removeItem('searchHistory');
            updateSearchHistory();
        }
    );
}

// Obtenir le nombre de résultats actuels
function getCurrentResultCount() {
    const resultsCount = document.getElementById('resultsCount').textContent;
    const match = resultsCount.match(/\((\d+)/);
    return match ? parseInt(match[1]) : 0;
}

// ==================== AMÉLIORATION DE L'EXPÉRIENCE DE RECHERCHE ====================
function enhanceSearchExperience() {
    const searchInput = document.getElementById('searchInput');
    const searchSuggestions = document.getElementById('searchSuggestions');
    
    // Suggestions lors de la saisie
    searchInput.addEventListener('input', function() {
        const query = this.value.toLowerCase();
        searchSuggestions.innerHTML = '';
        
        if (!query) {
            searchSuggestions.style.display = 'none';
            return;
        }
        
        // Suggestions de tags
        const tagSuggestions = Object.keys(tags)
            .filter(tag => tag.toLowerCase().includes(query))
            .slice(0, 3);
        
        // Suggestions de noms de fichiers
        const nameSuggestions = files
            .filter(file => file.name.toLowerCase().includes(query))
            .slice(0, 3)
            .map(file => file.name);
        
        // Combiner et afficher les suggestions
        const allSuggestions = [...tagSuggestions.map(tag => `#${tag}`), ...nameSuggestions];
        
        if (allSuggestions.length > 0) {
            searchSuggestions.style.display = 'block';
            
            allSuggestions.forEach(suggestion => {
                const suggestionItem = document.createElement('div');
                suggestionItem.className = 'suggestion-item';
                suggestionItem.textContent = suggestion;
                suggestionItem.addEventListener('click', () => {
                    searchInput.value = suggestion;
                    searchSuggestions.style.display = 'none';
                    performSearch();
                });
                searchSuggestions.appendChild(suggestionItem);
            });
        } else {
            searchSuggestions.style.display = 'none';
        }
    });
    
    // Masquer les suggestions quand on clique ailleurs
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchSuggestions.contains(e.target)) {
            searchSuggestions.style.display = 'none';
        }
    });
    
    // Recherche quand on appuie sur Entrée
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
}

// ==================== GESTION DE L'INTERFACE UTILISATEUR ====================
// Basculer entre les vues grille et liste
document.getElementById('toggleViewBtn').addEventListener('click', function() {
    isListView = !isListView;
    this.innerHTML = isListView ? '<i class="fas fa-th"></i>' : '<i class="fas fa-list"></i>';
    this.title = isListView ? 'Vue grille' : 'Vue liste';
    performSearch();
});

// Ouvrir le modal de collection
document.getElementById('createCollectionBtn').addEventListener('click', function() {
    resetCollectionForm();
    document.getElementById('collectionModal').style.display = 'flex';
});

// Fermer le modal de fichier
document.getElementById('closeModalBtn').addEventListener('click', function() {
    document.getElementById('fileModal').style.display = 'none';
    stopVideoPreviews();
});

// Fermer le modal de collection
document.getElementById('closeCollectionModalBtn').addEventListener('click', function() {
    document.getElementById('collectionModal').style.display = 'none';
    resetCollectionForm();
});

// Fermer le modal de confirmation
document.getElementById('closeConfirmModalBtn').addEventListener('click', function() {
    document.getElementById('confirmModal').style.display = 'none';
});

// Fermer les modals en cliquant à l'extérieur
window.addEventListener('click', function(e) {
    const fileModal = document.getElementById('fileModal');
    const collectionModal = document.getElementById('collectionModal');
    const confirmModal = document.getElementById('confirmModal');
    
    if (e.target === fileModal) {
        fileModal.style.display = 'none';
        stopVideoPreviews();
    }
    if (e.target === collectionModal) {
        collectionModal.style.display = 'none';
        resetCollectionForm();
    }
    if (e.target === confirmModal) {
        confirmModal.style.display = 'none';
    }
});

// Afficher le modal de confirmation
function showConfirmModal(title, message, confirmCallback) {
    document.getElementById('confirmModalTitle').textContent = title;
    document.getElementById('confirmModalMessage').textContent = message;
    document.getElementById('confirmModal').style.display = 'flex';
    
    // Supprimer les anciens événements
    const confirmBtn = document.getElementById('confirmActionBtn');
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    
    // Ajouter le nouvel événement
    newConfirmBtn.addEventListener('click', function() {
        document.getElementById('confirmModal').style.display = 'none';
        confirmCallback();
    });
}

// ==================== DONNÉES D'EXEMPLE ====================
// Fonction pour initialiser des données d'exemple
function initSampleData() {
    // Créer quelques collections d'exemple
    const sampleCollections = [
        {
            id: generateId('collection'),
            name: 'Projets Web',
            description: 'Tous mes projets de développement web',
            color: '#3498db',
            files: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        },
        {
            id: generateId('collection'),
            name: 'Photos de voyage',
            description: 'Mes meilleures photos de voyage',
            color: '#e74c3c',
            files: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        },
        {
            id: generateId('collection'),
            name: 'Documents importants',
            description: 'Documents administratifs et contrats',
            color: '#2ecc71',
            files: [],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString()
        }
    ];
    
    // Créer quelques fichiers d'exemple
    const sampleFiles = [
        {
            id: generateId('image'),
            name: 'Logo du site',
            description: 'Logo principal pour le projet client',
            type: 'image',
            location: 'https://via.placeholder.com/300x150/3498db/ffffff?text=Logo+Site',
            locationType: 'externe',
            views: 15,
            createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()
        },
        {
            id: generateId('document'),
            name: 'Cahier des charges',
            description: 'Spécifications techniques du projet',
            type: 'document',
            location: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
            locationType: 'externe',
            views: 42,
            createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString()
        },
        {
            id: generateId('video'),
            name: 'Démo du produit',
            description: 'Vidéo de présentation des fonctionnalités',
            type: 'video',
            location: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4',
            locationType: 'externe',
            views: 87,
            createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString()
        },
        {
            id: generateId('lien'),
            name: 'Documentation React',
            description: 'Lien vers la documentation officielle',
            type: 'lien',
            location: 'https://reactjs.org/docs/getting-started.html',
            locationType: 'externe',
            views: 23,
            createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()
        },
        {
            id: generateId('image'),
            name: 'Photo de montagne',
            description: 'Paysage des Alpes en été',
            type: 'image',
            location: 'https://via.placeholder.com/300x200/2ecc71/ffffff?text=Montagne',
            locationType: 'externe',
            views: 8,
            createdAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString()
        }
    ];
    
    // Associer les fichiers aux collections
    sampleFiles[0].collections = [sampleCollections[0].id];
    sampleFiles[1].collections = [sampleCollections[0].id, sampleCollections[2].id];
    sampleFiles[2].collections = [sampleCollections[0].id];
    sampleFiles[3].collections = [sampleCollections[0].id];
    sampleFiles[4].collections = [sampleCollections[1].id];
    
    // Ajouter les fichiers aux collections
    sampleFiles[0].collections.forEach(id => {
        const collection = sampleCollections.find(c => c.id === id);
        if (collection) {
            collection.files.push(sampleFiles[0].id);
        }
    });
    
    sampleFiles[1].collections.forEach(id => {
        const collection = sampleCollections.find(c => c.id === id);
        if (collection) {
            collection.files.push(sampleFiles[1].id);
        }
    });
    
    sampleFiles[2].collections.forEach(id => {
        const collection = sampleCollections.find(c => c.id === id);
        if (collection) {
            collection.files.push(sampleFiles[2].id);
        }
    });
    
    sampleFiles[3].collections.forEach(id => {
        const collection = sampleCollections.find(c => c.id === id);
        if (collection) {
            collection.files.push(sampleFiles[3].id);
        }
    });
    
    sampleFiles[4].collections.forEach(id => {
        const collection = sampleCollections.find(c => c.id === id);
        if (collection) {
            collection.files.push(sampleFiles[4].id);
        }
    });
    
    // Créer quelques tags d'exemple
    const sampleTags = {
        'web': [sampleFiles[0].id, sampleFiles[1].id, sampleFiles[2].id, sampleFiles[3].id],
        'design': [sampleFiles[0].id],
        'documentation': [sampleFiles[1].id, sampleFiles[3].id],
        'video': [sampleFiles[2].id],
        'voyage': [sampleFiles[4].id],
        'nature': [sampleFiles[4].id]
    };
    
    // Ajouter les données d'exemple aux tableaux principaux
    collections.push(...sampleCollections);
    files.push(...sampleFiles);
    Object.assign(tags, sampleTags);
    
    // Mettre à jour l'interface
    updateCollectionsList();
    updateCollectionsSelect();
    updateTagsCloud();
    performSearch();
    
    // Ajouter quelques recherches à l'historique
    searchHistory = [
        { query: 'web', timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), resultCount: 4 },
        { query: 'not(video)', timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(), resultCount: 4 },
        { query: '#design', timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), resultCount: 1 }
    ];
    updateSearchHistory();
}