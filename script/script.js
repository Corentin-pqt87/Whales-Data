// Structure de données pour stocker les objets, tags et collections
let files = [];
let tags = {};
let collections = [];
let currentFile = null;
let currentCollectionId = null;
let isListView = false;
let isEditingFile = false;
let isEditingCollection = false;

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

// Annuler l'édition
document.getElementById('cancelEditBtn').addEventListener('click', resetFileForm);

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

// Afficher un modal de confirmation
function showConfirmModal(title, message, confirmCallback) {
    document.getElementById('confirmModalTitle').textContent = title;
    document.getElementById('confirmModalMessage').textContent = message;
    document.getElementById('confirmModal').style.display = 'flex';
    
    const confirmBtn = document.getElementById('confirmActionBtn');
    const cancelBtn = document.getElementById('cancelActionBtn');
    
    // Supprimer les anciens événements
    const newConfirmBtn = confirmBtn.cloneNode(true);
    const newCancelBtn = cancelBtn.cloneNode(true);
    
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
    
    // Ajouter les nouveaux événements
    document.getElementById('confirmActionBtn').addEventListener('click', function() {
        confirmCallback();
        document.getElementById('confirmModal').style.display = 'none';
    });
    
    document.getElementById('cancelActionBtn').addEventListener('click', function() {
        document.getElementById('confirmModal').style.display = 'none';
    });
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
// Remplacer la fonction performSearch par cette version améliorée
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

// Nouvelle fonction pour gérer la recherche avancée avec NOT
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
// formater l'affichage des requêtes
function formatSearchQueryDisplay(query) {
    if (!query) return '';
    
    // Mettre en évidence les termes NOT
    return query
        .replace(/(not\([^)]+\))/gi, '<span style="color: var(--accent-color); font-weight: bold;">$1</span>')
        .replace(/(not\s+[^\s)]+)/gi, '<span style="color: var(--accent-color); font-weight: bold;">$1</span>');
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

// Afficher les statistiques
function showStats() {
    const statsModal = document.getElementById('statsModal');
    const totalFiles = document.getElementById('totalFiles');
    const totalTags = document.getElementById('totalTags');
    const totalViews = document.getElementById('totalViews');
    const totalCollections = document.getElementById('totalCollections');
    const popularFiles = document.getElementById('popularFiles');
    const popularCollections = document.getElementById('popularCollections');
    
    // Calculer les statistiques
    totalFiles.textContent = files.length;
    totalTags.textContent = Object.keys(tags).length;
    totalCollections.textContent = collections.length;
    
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
    
    // Afficher les collections les plus populaires
    popularCollections.innerHTML = '';
    const sortedCollections = [...collections]
        .filter(c => c.files && c.files.length > 0)
        .sort((a, b) => b.files.length - a.files.length)
        .slice(0, 5);
    
    if (sortedCollections.length === 0) {
        popularCollections.innerHTML = '<p>Aucune collection avec des fichiers.</p>';
    } else {
        sortedCollections.forEach(collection => {
            const collectionElement = document.createElement('div');
            collectionElement.className = 'popular-collection';
            collectionElement.innerHTML = `
                <div class="popular-collection-info">
                    <strong>${collection.name}</strong>
                </div>
                <div class="popular-collection-count">
                    <i class="fas fa-file"></i> ${collection.files.length} fichiers
                </div>
            `;
            popularCollections.appendChild(collectionElement);
        });
    }
    
    statsModal.style.display = 'flex';
}

// Sauvegarder les données dans un fichier
function saveData() {
    const data = {
        files,
        tags,
        collections
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
                    collections = data.collections || [];
                    
                    updateCollectionsList();
                    updateCollectionsSelect();
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
    // Ajouter quelques recherches d'exemple
    // Ajouter des recherches d'exemple réalistes
    searchHistory = [
        {
            query: 'image vacances',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            resultCount: 3
        },
        {
            query: 'video randonnée',
            timestamp: new Date(Date.now() - 86400000).toISOString(),
            resultCount: 1
        },
        {
            query: 'image not(video)',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
            resultCount: 3
        },
        {
            query: 'document travail',
            timestamp: new Date(Date.now() - 259200000).toISOString(),
            resultCount: 1
        }
    ];
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
            location: 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf',
            locationType: 'externe',
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
    
    // Création de collections exemple
    collections = [
        {
            id: generateId('collection'),
            name: 'Vacances',
            description: 'Photos et vidéos de vacances',
            color: '#e74c3c',
            files: [sampleFiles[0].id, sampleFiles[1].id, sampleFiles[4].id],
            createdAt: '2023-01-15T10:30:00Z',
            updatedAt: '2023-06-18T11:20:00Z'
        },
        {
            id: generateId('collection'),
            name: 'Travail',
            description: 'Documents professionnels',
            color: '#3498db',
            files: [sampleFiles[2].id],
            createdAt: '2023-03-10T09:15:00Z',
            updatedAt: '2023-03-10T09:15:00Z'
        },
        {
            id: generateId('collection'),
            name: 'Nature',
            description: 'Photos de paysages naturels',
            color: '#27ae60',
            files: [sampleFiles[0].id, sampleFiles[4].id, sampleFiles[5].id],
            createdAt: '2023-05-12T18:30:00Z',
            updatedAt: '2023-06-18T11:20:00Z'
        }
    ];
    
    // Associer les collections aux fichiers
    sampleFiles[0].collections = [collections[0].id, collections[2].id];
    sampleFiles[1].collections = [collections[0].id];
    sampleFiles[2].collections = [collections[1].id];
    sampleFiles[4].collections = [collections[0].id, collections[2].id];
    sampleFiles[5].collections = [collections[2].id];
    
    // Affichage initial
    updateCollectionsList();
    updateCollectionsSelect();
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

// Ajouter cette variable globale
let searchHistory = [];

// Ajouter cette fonction pour gérer l'historique
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

// Ajouter cette fonction pour mettre à jour l'affichage de l'historique
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

// Ajouter cette fonction pour effacer tout l'historique
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

// Ajouter cette fonction pour améliorer l'expérience utilisateur
function enhanceSearchExperience() {
    const searchInput = document.getElementById('searchInput');
    
    // Focus sur le champ de recherche quand on appuie sur Ctrl+K
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            searchInput.focus();
        }
        
        // Effacer la recherche avec Escape
        if (e.key === 'Escape' && document.activeElement === searchInput) {
            searchInput.value = '';
            performSearch();
        }
    });
    
    // Afficher un placeholder avancé avec les nouvelles fonctionnalités
    searchInput.placeholder = 'Ex: image #vacances not(travail) • Ctrl+K pour focus';
}

// Ajouter l'événement pour le bouton d'effacement
document.getElementById('clearHistoryBtn').addEventListener('click', clearSearchHistory);

// Ajouter cette fonction pour formater la date
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
// Ajouter cette fonction pour tronquer le texte
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Ajouter cette fonction pour supprimer de l'historique
function removeFromSearchHistory(index) {
    searchHistory.splice(index, 1);
    localStorage.setItem('searchHistory', JSON.stringify(searchHistory));
    updateSearchHistory();
}

// Ajouter cette fonction pour obtenir le nombre de résultats actuels
function getCurrentResultCount() {
    const resultsContainer = document.getElementById('resultsContainer');
    return resultsContainer.querySelectorAll('.file-card').length;
}
// Ajouter cette fonction pour charger l'historique au démarrage
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
    }
    updateSearchHistory();
}


// Bouton pour basculer entre la vue grille et la vue liste
document.getElementById('toggleViewBtn').addEventListener('click', function() {
    isListView = !isListView;
    this.innerHTML = isListView ? 
        '<i class="fas fa-th-large"></i> Vue grille' : 
        '<i class="fas fa-th"></i> Vue liste';
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
    
    const collectionModal = document.getElementById('collectionModal');
    if (e.target === collectionModal) {
        collectionModal.style.display = 'none';
    }
    
    const confirmModal = document.getElementById('confirmModal');
    if (e.target === confirmModal) {
        confirmModal.style.display = 'none';
    }
});

// Afficher les statistiques
document.getElementById('viewStatsBtn').addEventListener('click', showStats);

// Fermer le modal des statistiques
document.getElementById('closeStatsModal').addEventListener('click', function() {
    document.getElementById('statsModal').style.display = 'none';
});

// Ouvrir le modal de création de collection
document.getElementById('addCollectionBtn').addEventListener('click', function() {
    resetCollectionForm();
    document.getElementById('collectionModal').style.display = 'flex';
});

// Fermer le modal de collection
document.getElementById('closeCollectionModal').addEventListener('click', function() {
    document.getElementById('collectionModal').style.display = 'none';
});

// Supprimer une collection
document.getElementById('deleteCollectionBtn').addEventListener('click', function() {
    const collectionId = document.getElementById('collectionId').value;
    if (collectionId) {
        document.getElementById('collectionModal').style.display = 'none';
        deleteCollection(collectionId);
    }
});

// Fermer le modal de confirmation
document.getElementById('closeConfirmModal').addEventListener('click', function() {
    document.getElementById('confirmModal').style.display = 'none';
});

// Sauvegarder les données
document.getElementById('saveDataBtn').addEventListener('click', saveData);

// Charger les données
document.getElementById('loadDataBtn').addEventListener('click', loadData);

// Initialisation
// Ajouter l'appel au chargement de l'historique au démarrage
document.addEventListener('DOMContentLoaded', function() {
    loadSearchHistory();
    enhanceSearchExperience();
    // ... le reste de l'initialisation ...
});
initSampleData();