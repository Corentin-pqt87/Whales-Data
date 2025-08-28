import os
import json
import uuid
import re
import datetime
from collections import deque
from typing import List, Dict, Set, Optional, Union
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel, 
                             QTextEdit, QComboBox, QFileDialog, QMessageBox, QSplitter,
                             QTreeWidget, QTreeWidgetItem, QTabWidget, QGroupBox, QDialog,
                             QMenu, QAction, QCompleter, QInputDialog, QProgressDialog,
                             QCheckBox)
from PyQt5.QtCore import Qt, QUrl, QSettings, QStringListModel
from PyQt5.QtGui import QIcon, QFont, QDesktopServices, QPixmap, QPalette, QColor

class Config:
    """Classe de configuration pour gérer les préférences"""
    def __init__(self):
        self.settings = QSettings("TagManager", "FileTagDatabase")
    
    def get_data_dir(self):
        """Retourne le dossier de données configuré"""
        return self.settings.value("data_directory", "data", type=str)
    
    def set_data_dir(self, path):
        """Définit le dossier de données"""
        self.settings.setValue("data_directory", path)
    
    def is_first_run(self):
        """Vérifie si c'est le premier démarrage"""
        return self.settings.value("first_run", True, type=bool)
    
    def set_first_run_complete(self):
        """Marque le premier démarrage comme terminé"""
        self.settings.setValue("first_run", False)
    
    def get_theme_file(self):
        """Retourne le chemin du fichier de thème"""
        data_dir = self.get_data_dir()
        return os.path.join(data_dir, "theme.css")

    def get_dark_mode(self):
        """Retourne l'état du mode sombre"""
        return self.settings.value("dark_mode", False, type=bool)
    
    def set_dark_mode(self, enabled):
        """Définit l'état du mode sombre"""
        self.settings.setValue("dark_mode", enabled)
    
    def get_history_file(self):
        """Retourne le chemin du fichier d'historique"""
        data_dir = self.get_data_dir()
        return os.path.join(data_dir, "search_history.json")

class Collection:
    """Représente une collection d'objets"""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.id = f"collection_{uuid.uuid4().hex[:8]}"
        self.object_ids: Set[str] = set()
        self.created_at = datetime.datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def to_dict(self):
        """Convertit la collection en dictionnaire pour sérialisation"""
        return {
            "name": self.name,
            "description": self.description,
            "id": self.id,
            "object_ids": list(self.object_ids),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def add_object(self, obj_id: str):
        """Ajoute un objet à la collection"""
        self.object_ids.add(obj_id)
        self.updated_at = datetime.datetime.now().isoformat()
    
    def remove_object(self, obj_id: str):
        """Retire un objet de la collection"""
        if obj_id in self.object_ids:
            self.object_ids.remove(obj_id)
            self.updated_at = datetime.datetime.now().isoformat()
    
    def contains_object(self, obj_id: str) -> bool:
        """Vérifie si la collection contient un objet"""
        return obj_id in self.object_ids

class SearchHistory:
    """Gère l'historique des recherches"""
    def __init__(self, max_history=50):
        self.max_history = max_history
        self.history = deque(maxlen=max_history)
    
    def add_search(self, query):
        """Ajoute une recherche à l'historique"""
        if query and query.strip():
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.history.appendleft((timestamp, query.strip()))
    
    def get_recent_searches(self, limit=10):
        """Retourne les recherches récentes"""
        return list(self.history)[:limit]
    
    def clear_history(self):
        """Efface tout l'historique"""
        self.history.clear()
    
    def save_to_file(self, file_path):
        """Sauvegarde l'historique dans un fichier"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(list(self.history), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de l'historique: {e}")
    
    def load_from_file(self, file_path):
        """Charge l'historique depuis un fichier"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    self.history = deque(history_data, maxlen=self.max_history)
        except Exception as e:
            print(f"Erreur lors du chargement de l'historique: {e}")

class FileObject:
    def __init__(self, name: str, description: str, file_type: str, location: str):
        self.name = name
        self.description = description
        self.file_type = file_type
        self.location = location
        self.id = self.generate_id(file_type)
    
    def generate_id(self, file_type: str) -> str:
        """Génère un ID unique avec préfixe selon le type et suffixe aléatoire"""
        type_prefix = self.get_type_prefix(file_type)
        random_suffix = str(uuid.uuid4().int)[:16]  # 16 chiffres aléatoires
        return f"{type_prefix}_{random_suffix}"
    
    def get_type_prefix(self, file_type: str) -> str:
        """Retourne le préfixe selon le type de fichier"""
        prefixes = {
            "image": "1",
            "video": "2",
            "audio": "3",
            "document": "4"
        }
        return prefixes.get(file_type.lower(), "0")  # 0 pour type inconnu
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour sérialisation"""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.file_type,
            "id": self.id,
            "location": self.location
        }
    
    def is_external(self):
        """Détermine si l'emplacement est externe (URL web)"""
        return self.location.startswith(('http://', 'https://', 'www.'))
    
    def open_location(self):
        """Ouvre l'emplacement du fichier (local ou web)"""
        try:
            if self.is_external():
                # Ouvrir une URL web
                url = QUrl(self.location)
                if not self.location.startswith(('http://', 'https://')):
                    url = QUrl("https://" + self.location)
                return QDesktopServices.openUrl(url)
            else:
                # Ouvrir un fichier local
                if os.path.exists(self.location):
                    # Utiliser QUrl.fromLocalFile pour les chemins locaux
                    return QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(self.location)))
                else:
                    # Si le fichier n'existe pas, ouvrir le dossier parent
                    parent_dir = os.path.dirname(os.path.abspath(self.location))
                    if os.path.exists(parent_dir):
                        return QDesktopServices.openUrl(QUrl.fromLocalFile(parent_dir))
                    return False
        except Exception as e:
            print(f"Erreur lors de l'ouverture: {e}")
            return False

class TagDatabase:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.objects_dir = os.path.join(data_dir, "Objects")
        self.tags_dir = os.path.join(data_dir, "Tags")
        self.collections_dir = os.path.join(data_dir, "Collections")  # Nouveau dossier pour les collections
        self.objects: Dict[str, FileObject] = {}  # ID -> FileObject
        self.tags: Dict[str, Set[str]] = {}       # Tag -> Set d'IDs
        self.tag_files: Dict[str, str] = {}       # Tag -> Chemin du fichier
        self.collections: Dict[str, Collection] = {}  # ID -> Collection
        
        # Créer les répertoires de données s'ils n'existent pas
        os.makedirs(self.objects_dir, exist_ok=True)
        os.makedirs(self.tags_dir, exist_ok=True)
        os.makedirs(self.collections_dir, exist_ok=True)  # Créer le dossier collections
        self.load_data()
    
    def load_data(self):
        """Charge les données depuis les fichiers JSON"""
        # Charger les objets
        if os.path.exists(self.objects_dir):
            for filename in os.listdir(self.objects_dir):
                if filename.endswith(".json"):
                    try:
                        with open(os.path.join(self.objects_dir, filename), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            obj = FileObject(
                                data["name"], 
                                data["description"], 
                                data["type"], 
                                data["location"]
                            )
                            obj.id = data["id"]
                            self.objects[obj.id] = obj
                    except Exception as e:
                        print(f"Erreur lors du chargement de {filename}: {e}")
        
        # Charger les tags
        if os.path.exists(self.tags_dir):
            for filename in os.listdir(self.tags_dir):
                if filename.endswith(".json"):
                    try:
                        tag_name = filename[:-5]  # Enlever ".json"
                        with open(os.path.join(self.tags_dir, filename), 'r', encoding='utf-8') as f:
                            obj_ids = json.load(f)
                            self.tags[tag_name] = set(obj_ids)
                            self.tag_files[tag_name] = os.path.join(self.tags_dir, filename)
                    except Exception as e:
                        print(f"Erreur lors du chargement du tag {filename}: {e}")
        
        # Charger les collections
        if os.path.exists(self.collections_dir):
            for filename in os.listdir(self.collections_dir):
                if filename.endswith(".json"):
                    try:
                        with open(os.path.join(self.collections_dir, filename), 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            collection = Collection(data["name"], data["description"])
                            collection.id = data["id"]
                            collection.object_ids = set(data["object_ids"])
                            collection.created_at = data["created_at"]
                            collection.updated_at = data["updated_at"]
                            self.collections[collection.id] = collection
                    except Exception as e:
                        print(f"Erreur lors du chargement de la collection {filename}: {e}")
    
    def add_object(self, obj: FileObject) -> Optional[str]:
        """Ajoute un objet à la base de données si l'emplacement n'existe pas déjà"""
        if self.location_exists(obj.location):
            return None  # Retourne None si doublon
        
        self.objects[obj.id] = obj
        self.save_object(obj)
        return obj.id
    
    def update_object(self, obj_id: str, name: str, description: str, file_type: str, location: str) -> bool:
        """Met à jour un objet existant en vérifiant les doublons"""
        if obj_id not in self.objects:
            return False

        # Vérifier si le nouvel emplacement existe déjà pour un autre objet
        if location != self.objects[obj_id].location:  # Seulement si l'emplacement change
            if self.location_exists(location):
                return False

        # Mettre à jour les propriétés de l'objet
        self.objects[obj_id].name = name
        self.objects[obj_id].description = description
        self.objects[obj_id].file_type = file_type
        self.objects[obj_id].location = location

        # Sauvegarder les modifications
        self.save_object(self.objects[obj_id])
        return True
    
    def delete_object(self, obj_id: str) -> bool:
        """Supprime un objet de la base de données"""
        if obj_id not in self.objects:
            return False
        
        # Retirer l'objet de tous les tags
        for tag in self.get_object_tags(obj_id):
            self.remove_tag(obj_id, tag)
        
        # Retirer l'objet de toutes les collections
        for collection in self.collections.values():
            if collection.contains_object(obj_id):
                collection.remove_object(obj_id)
                self.save_collection(collection)
        
        # Supprimer le fichier de l'objet
        obj_file = os.path.join(self.objects_dir, f"{obj_id}.json")
        if os.path.exists(obj_file):
            try:
                os.remove(obj_file)
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier {obj_file}: {e}")
        
        # Retirer l'objet de la mémoire
        del self.objects[obj_id]
        return True
    
    def save_object(self, obj: FileObject) -> None:
        """Sauvegarde un objet dans un fichier JSON"""
        obj_path = os.path.join(self.objects_dir, f"{obj.id}.json")
        with open(obj_path, 'w', encoding='utf-8') as f:
            json.dump(obj.to_dict(), f, ensure_ascii=False, indent=4)
    
    def add_tag(self, obj_id: str, tag: str) -> None:
        """Ajoute un tag à un objet"""
        # Nettoyer le tag (enlever le # s'il est présent)
        clean_tag = tag.lstrip('#').strip().replace(' ', '_')
        
        if not clean_tag:
            return
        
        # Créer le fichier de tag s'il n'existe pas
        if clean_tag not in self.tags:
            self.tags[clean_tag] = set()
            tag_file_path = os.path.join(self.tags_dir, f"{clean_tag}.json")
            self.tag_files[clean_tag] = tag_file_path
        
        # Ajouter l'ID à l'ensemble des IDs pour ce tag
        self.tags[clean_tag].add(obj_id)
        
        # Sauvegarder le tag
        self.save_tag(clean_tag)
    
    def remove_tag(self, obj_id: str, tag: str) -> None:
        """Retire un tag d'un objet"""
        clean_tag = tag.lstrip('#')
        if clean_tag in self.tags and obj_id in self.tags[clean_tag]:
            self.tags[clean_tag].remove(obj_id)
            self.save_tag(clean_tag)
    
    def save_tag(self, tag: str) -> None:
        """Sauvegarde un tag dans un fichier JSON"""
        if tag in self.tags:
            tag_file_path = self.tag_files[tag]
            with open(tag_file_path, 'w', encoding='utf-8') as f:
                json.dump(list(self.tags[tag]), f, ensure_ascii=False, indent=4)
    
    # Méthodes pour les collections
    def create_collection(self, name: str, description: str = "") -> Optional[Collection]:
        """Crée une nouvelle collection"""
        if not name.strip():
            return None
        
        # Vérifier si une collection avec le même nom existe déjà
        for collection in self.collections.values():
            if collection.name.lower() == name.lower():
                return None
        
        collection = Collection(name, description)
        self.collections[collection.id] = collection
        self.save_collection(collection)
        return collection
    
    def delete_collection(self, collection_id: str) -> bool:
        """Supprime une collection"""
        if collection_id not in self.collections:
            return False
        
        # Supprimer le fichier de la collection
        collection_file = os.path.join(self.collections_dir, f"{collection_id}.json")
        if os.path.exists(collection_file):
            try:
                os.remove(collection_file)
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier {collection_file}: {e}")
        
        # Retirer la collection de la mémoire
        del self.collections[collection_id]
        return True
    
    def save_collection(self, collection: Collection) -> None:
        """Sauvegarde une collection dans un fichier JSON"""
        collection_path = os.path.join(self.collections_dir, f"{collection.id}.json")
        with open(collection_path, 'w', encoding='utf-8') as f:
            json.dump(collection.to_dict(), f, ensure_ascii=False, indent=4)
    
    def add_object_to_collection(self, obj_id: str, collection_id: str) -> bool:
        """Ajoute un objet à une collection"""
        if obj_id not in self.objects or collection_id not in self.collections:
            return False
        
        collection = self.collections[collection_id]
        collection.add_object(obj_id)
        self.save_collection(collection)
        return True
    
    def remove_object_from_collection(self, obj_id: str, collection_id: str) -> bool:
        """Retire un objet d'une collection"""
        if collection_id not in self.collections:
            return False
        
        collection = self.collections[collection_id]
        collection.remove_object(obj_id)
        self.save_collection(collection)
        return True
    
    def get_collections_for_object(self, obj_id: str) -> List[Collection]:
        """Retourne toutes les collections contenant un objet"""
        return [collection for collection in self.collections.values() 
                if collection.contains_object(obj_id)]
    
    def search_by_collection(self, collection_name: str) -> List[FileObject]:
        """Recherche des objets par nom de collection"""
        results = []
        for collection in self.collections.values():
            if collection_name.lower() in collection.name.lower():
                for obj_id in collection.object_ids:
                    if obj_id in self.objects:
                        results.append(self.objects[obj_id])
        return results
    
    def search_by_name(self, name: str) -> List[FileObject]:
        """Recherche des objets par nom (recherche partielle insensible à la casse)"""
        results = []
        search_terms = name.lower().split()
        
        for obj in self.objects.values():
            obj_name_lower = obj.name.lower()
            # Vérifie si tous les termes de recherche sont présents dans le nom
            if all(term in obj_name_lower for term in search_terms):
                results.append(obj)
        
        return results
    
    def search_by_tag(self, tag: str) -> List[FileObject]:
        """Recherche des objets por tag"""
        clean_tag = tag.lstrip('#').strip().replace(' ', '_')
        if clean_tag not in self.tags:
            return []
        
        results = []
        for obj_id in self.tags[clean_tag]:
            if obj_id in self.objects:
                results.append(self.objects[obj_id])
        return results
    
    def get_object_tags(self, obj_id: str) -> List[str]:
        """Retourne tous les tags associés à un objet"""
        tags = []
        for tag, obj_ids in self.tags.items():
            if obj_id in obj_ids:
                tags.append(tag)
        return tags
    
    def advanced_search(self, query: str) -> List[FileObject]:
        """Recherche avancée avec syntaxe booléenne complète"""
        if not query.strip():
            return list(self.objects.values())
        
        try:
            # Parser la requête booléenne
            parsed_query = self.parse_boolean_query(query)
            
            # Évaluer la requête
            result_ids = self.evaluate_boolean_expression(parsed_query)
            
            # Convertir les IDs en objets
            results = []
            for obj_id in result_ids:
                if obj_id in self.objects:
                    results.append(self.objects[obj_id])
            
            return results
            
        except Exception as e:
            print(f"Erreur dans la recherche avancée: {e}")
            # Fallback vers la recherche simple
            return self.search_by_name(query)
    
    def location_exists(self, location: str) -> bool:
        """Vérifie si un emplacement existe déjà dans la base de données"""
        for obj in self.objects.values():
            if obj.location == location:
                return True
        return False

    def get_object_by_location(self, location: str) -> Optional[FileObject]:
        """Retourne l'objet correspondant à un emplacement"""
        for obj in self.objects.values():
            if obj.location == location:
                return obj
        return None
    
    def parse_boolean_query(self, query: str) -> Union[str, dict]:
        """
        Parse une requête booléenne en arbre syntaxique
        Format: {"operator": "AND/OR/NOT", "operands": [operand1, operand2, ...]}
        """
        query = query.strip()
        
        # Gérer les parenthèses
        if query.startswith('(') and query.endswith(')'):
            return self.parse_boolean_query(query[1:-1])
        
        # Chercher les opérateurs en respectant la priorité (NOT > AND > OR)
        # D'abord chercher les opérateurs avec espaces
        for operator in [' OR ', ' AND ', ' NOT ']:
            if operator in query:
                parts = query.split(operator, 1)
                if len(parts) == 2:
                    left, right = parts
                    return {
                        "operator": operator.strip(),
                        "operands": [
                            self.parse_boolean_query(left),
                            self.parse_boolean_query(right)
                        ]
                    }
        
        # Ensuite chercher les opérateurs sans espaces (pour la compatibilité)
        for operator in ['OR', 'AND', 'NOT']:
            if f" {operator} " in query:  # Éviter les matches dans les mots
                continue
            if operator in query:
                # Vérifier que c'est bien un opérateur et pas une partie d'un mot
                pattern = r'(?<!\w)' + re.escape(operator) + r'(?!\w)'
                if re.search(pattern, query):
                    parts = re.split(pattern, query, 1)
                    if len(parts) == 2:
                        left, right = parts
                        return {
                            "operator": operator,
                            "operands": [
                                self.parse_boolean_query(left),
                                self.parse_boolean_query(right)
                            ]
                        }
        
        # Si pas d'opérateur, c'est un terme simple
        return query.strip()
    
    def evaluate_boolean_expression(self, expression: Union[str, dict]) -> Set[str]:
        """Évalue une expression booléenne et retourne les IDs d'objets correspondants"""
        if isinstance(expression, str):
            # Terme simple - recherche par nom ou tag
            return self.evaluate_simple_term(expression)
        
        operator = expression["operator"]
        operands = expression["operands"]
        
        if operator == "NOT":
            if len(operands) != 2:  # NOT a deux opérandes mais le second est ignoré
                # Pour gérer "NOT terme" et "terme NOT autre"
                if len(operands) == 1:
                    # Cas: NOT terme
                    result = self.evaluate_boolean_expression(operands[0])
                    return self.get_all_object_ids() - result
                else:
                    raise ValueError("NOT doit avoir un ou deux opérandes")
            
            # Cas: terme1 NOT terme2
            result1 = self.evaluate_boolean_expression(operands[0])
            result2 = self.evaluate_boolean_expression(operands[1])
            return result1 - result2
        
        elif operator == "AND":
            if len(operands) < 2:
                raise ValueError("AND doit avoir au moins deux opérandes")
            
            results = []
            for operand in operands:
                results.append(self.evaluate_boolean_expression(operand))
            
            # Intersection de tous les résultats
            return set.intersection(*results)
        
        elif operator == "OR":
            if len(operands) < 2:
                raise ValueError("OR doit avoir au moins deux opérandes")
            
            results = set()
            for operand in operands:
                results.update(self.evaluate_boolean_expression(operand))
            
            return results
        
        else:
            raise ValueError(f"Opérateur inconnu: {operator}")
    
    def evaluate_simple_term(self, term: str) -> Set[str]:
        """Évalue un terme simple (nom ou tag)"""
        term = term.strip()
        
        # Terme entre guillemets (recherche exacte)
        if term.startswith('"') and term.endswith('"'):
            exact_term = term[1:-1]
            return self.search_exact_name(exact_term)
        
        # Tag (commence par #)
        elif term.startswith('#'):
            tag_name = term[1:].strip()
            objects = self.search_by_tag(tag_name)
            return {obj.id for obj in objects}
        
        # Collection (commence par @)
        elif term.startswith('@'):
            collection_name = term[1:].strip()
            objects = self.search_by_collection(collection_name)
            return {obj.id for obj in objects}
        
        # Recherche par nom (avec wildcards)
        else:
            objects = self.search_by_name(term)
            return {obj.id for obj in objects}
    
    def search_exact_name(self, name: str) -> Set[str]:
        """Recherche exacte par nom (insensible à la casse)"""
        results = set()
        name_lower = name.lower()
        
        for obj_id, obj in self.objects.items():
            if obj.name.lower() == name_lower:
                results.add(obj_id)
        
        return results
    
    def get_all_object_ids(self) -> Set[str]:
        """Retourne tous les IDs d'objets"""
        return set(self.objects.keys())
    
    def search_by_name_with_wildcards(self, pattern: str) -> Set[str]:
        """
        Recherche par nom avec wildcards (* pour plusieurs caractères, ? pour un caractère)
        """
        results = set()
        pattern_lower = pattern.lower()
        
        # Convertir le pattern en regex
        regex_pattern = pattern_lower.replace('*', '.*').replace('?', '.')
        regex_pattern = f"^{regex_pattern}$"
        
        try:
            import re
            regex = re.compile(regex_pattern)
            
            for obj_id, obj in self.objects.items():
                if regex.match(obj.name.lower()):
                    results.add(obj_id)
                    
        except re.error:
            # Fallback vers la recherche simple si le pattern est invalide
            return self.evaluate_simple_term(pattern)
        
        return results

class CollectionDialog(QDialog):
    """Boîte de dialogue pour créer ou modifier une collection"""
    def __init__(self, parent=None, collection=None):
        super().__init__(parent)
        self.collection = collection
        if collection:
            self.setWindowTitle("Modifier la collection")
            self.is_edit = True
        else:
            self.setWindowTitle("Créer une nouvelle collection")
            self.is_edit = False
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Nom de la collection
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nom de la collection:"))
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Description
        description_layout = QVBoxLayout()
        description_layout.addWidget(QLabel("Description:"))
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        description_layout.addWidget(self.description_input)
        layout.addLayout(description_layout)
        
        # Remplir les champs si on est en mode édition
        if self.is_edit and self.collection:
            self.name_input.setText(self.collection.name)
            self.description_input.setPlainText(self.collection.description)
        
        # Boutons
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
    
    def get_data(self):
        """Retourne les données saisies"""
        return {
            "name": self.name_input.text().strip(),
            "description": self.description_input.toPlainText().strip()
        }

class CollectionsDialog(QDialog):
    """Boîte de dialogue pour gérer les collections"""
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Gestion des collections")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        self.init_ui()
        self.load_collections()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Boutons d'action
        action_layout = QHBoxLayout()
        self.create_button = QPushButton("Nouvelle collection")
        self.create_button.clicked.connect(self.create_collection)
        self.edit_button = QPushButton("Modifier")
        self.edit_button.clicked.connect(self.edit_collection)
        self.delete_button = QPushButton("Supprimer")
        self.delete_button.clicked.connect(self.delete_collection)
        self.view_button = QPushButton("Voir les objets")
        self.view_button.clicked.connect(self.view_collection_objects)
        
        action_layout.addWidget(self.create_button)
        action_layout.addWidget(self.edit_button)
        action_layout.addWidget(self.delete_button)
        action_layout.addWidget(self.view_button)
        layout.addLayout(action_layout)
        
        # Liste des collections
        self.collections_list = QListWidget()
        self.collections_list.itemSelectionChanged.connect(self.update_buttons)
        self.collections_list.itemDoubleClicked.connect(self.view_collection_objects)
        layout.addWidget(self.collections_list)
        
        # Informations sur la collection sélectionnée
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # Boutons de fermeture
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.update_buttons()
    
    def load_collections(self):
        """Charge la liste des collections"""
        self.collections_list.clear()
        if not self.db:
            return
        
        for collection in self.db.collections.values():
            item = QListWidgetItem(f"{collection.name} ({len(collection.object_ids)} objets)")
            item.setData(Qt.UserRole, collection.id)
            self.collections_list.addItem(item)
    
    def update_buttons(self):
        """Met à jour l'état des boutons selon la sélection"""
        has_selection = self.collections_list.currentItem() is not None
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        self.view_button.setEnabled(has_selection)
        
        # Afficher les informations de la collection sélectionnée
        if has_selection:
            collection_id = self.collections_list.currentItem().data(Qt.UserRole)
            collection = self.db.collections.get(collection_id)
            if collection:
                self.info_label.setText(
                    f"Description: {collection.description}\n"
                    f"Créée le: {collection.created_at}\n"
                    f"Modifiée le: {collection.updated_at}\n"
                    f"Nombre d'objets: {len(collection.object_ids)}"
                )
        else:
            self.info_label.clear()
    
    def create_collection(self):
        """Crée une nouvelle collection"""
        dialog = CollectionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data["name"]:
                collection = self.db.create_collection(data["name"], data["description"])
                if collection:
                    self.load_collections()
                    QMessageBox.information(self, "Succès", "Collection créée avec succès.")
                else:
                    QMessageBox.warning(self, "Erreur", "Une collection avec ce nom existe déjà.")
    
    def edit_collection(self):
        """Modifie la collection sélectionnée"""
        item = self.collections_list.currentItem()
        if not item:
            return
        
        collection_id = item.data(Qt.UserRole)
        collection = self.db.collections.get(collection_id)
        if not collection:
            return
        
        dialog = CollectionDialog(self, collection)
        if dialog.exec() == QDialog.Acepted:
            data = dialog.get_data()
            if data["name"]:
                # Vérifier si le nouveau nom n'est pas déjà utilisé par une autre collection
                for col in self.db.collections.values():
                    if col.id != collection_id and col.name.lower() == data["name"].lower():
                        QMessageBox.warning(self, "Erreur", "Une collection avec ce nom existe déjà.")
                        return
                
                collection.name = data["name"]
                collection.description = data["description"]
                collection.updated_at = datetime.datetime.now().isoformat()
                self.db.save_collection(collection)
                self.load_collections()
                QMessageBox.information(self, "Succès", "Collection modifiée avec succès.")
    
    def delete_collection(self):
        """Supprime la collection sélectionnée"""
        item = self.collections_list.currentItem()
        if not item:
            return
        
        collection_id = item.data(Qt.UserRole)
        collection = self.db.collections.get(collection_id)
        if not collection:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer la collection '{collection.name}' ?\n"
            f"Cette action est irréversible mais ne supprime pas les objets.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.db.delete_collection(collection_id)
            if success:
                self.load_collections()
                QMessageBox.information(self, "Succès", "Collection supprimée avec succès.")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de supprimer la collection.")
    
    def view_collection_objects(self):
        """Affiche les objets de la collection sélectionnée"""
        item = self.collections_list.currentItem()
        if not item:
            return
        
        collection_id = item.data(Qt.UserRole)
        collection = self.db.collections.get(collection_id)
        if not collection:
            return
        
        # Créer une boîte de dialogue pour afficher les objets
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Objets de la collection: {collection.name}")
        dialog.setModal(True)
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Liste des objets
        objects_list = QListWidget()
        
        for obj_id in collection.object_ids:
            obj = self.db.objects.get(obj_id)
            if obj:
                item = QListWidgetItem(f"{obj.name} ({obj.file_type})")
                item.setData(Qt.UserRole, obj_id)
                objects_list.addItem(item)
        
        layout.addWidget(QLabel(f"Objets dans la collection ({len(collection.object_ids)}):"))
        layout.addWidget(objects_list)
        
        # Boutons
        button_layout = QHBoxLayout()
        remove_button = QPushButton("Retirer l'objet sélectionné")
        remove_button.clicked.connect(lambda: self.remove_object_from_collection(objects_list, collection))
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(dialog.accept)
        
        button_layout.addWidget(remove_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def remove_object_from_collection(self, objects_list, collection):
        """Retire l'objet sélectionné de la collection"""
        item = objects_list.currentItem()
        if not item:
            return
        
        obj_id = item.data(Qt.UserRole)
        success = self.db.remove_object_from_collection(obj_id, collection.id)
        if success:
            # Mettre à jour la liste
            row = objects_list.row(item)
            objects_list.takeItem(row)
            QMessageBox.information(self, "Succès", "Objet retiré de la collection.")
        else:
            QMessageBox.warning(self, "Erreur", "Impossible de retirer l'objet de la collection.")

class PreviewWidget(QWidget):
    """Widget pour afficher la prévisualisation des fichiers"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Titre
        self.title_label = QLabel("Prévisualisation")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)
        
        # Zone de prévisualisation
        self.preview_area = QLabel()
        self.preview_area.setAlignment(Qt.AlignCenter)
        self.preview_area.setMinimumSize(300, 200)
        self.preview_area.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                background-color: #f8f9fa;
                border-radius: 5px;
            }
        """)
        self.preview_area.setText("Aucune prévisualisation disponible")
        layout.addWidget(self.preview_area)
        
        # Informations supplémentaires
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
    
    def clear_preview(self):
        """Efface la prévisualisation"""
        self.preview_area.clear()
        self.preview_area.setText("Aucune prévisualisation disponible")
        self.info_label.clear()
    
    def set_preview(self, obj: FileObject):
        """Définit la prévisualisation pour un objet"""
        self.clear_preview()
        
        if obj.is_external():
            # Pour les URLs externes
            self.preview_area.setText("🌐 Lien externe\n\nCliquez sur 'Ouvrir' pour visiter le site")
            self.info_label.setText(f"URL: {obj.location}")
        else:
            # Pour les fichiers locaux
            file_path = obj.location
            if os.path.exists(file_path):
                file_ext = os.path.splitext(file_path)[1].lower()
                
                # Prévisualisation des images
                if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
                    try:
                        pixmap = QPixmap(file_path)
                        if not pixmap.isNull():
                            # Redimensionner pour s'adapter à la zone de prévisualisation
                            scaled_pixmap = pixmap.scaled(
                                self.preview_area.width() - 20,
                                self.preview_area.height() - 20,
                                Qt.KeepAspectRatio,
                                Qt.SmoothTransformation
                            )
                            self.preview_area.setPixmap(scaled_pixmap)
                            self.info_label.setText(f"Image: {os.path.basename(file_path)}\nTaille: {pixmap.width()}x{pixmap.height()}")
                        else:
                            self.preview_area.setText("❌ Impossible de charger l'image")
                    except Exception as e:
                        self.preview_area.setText("❌ Erreur de chargement")
                        self.info_label.setText(str(e))
                
                # Autres types de fichiers
                elif file_ext in ['.mp4', '.avi', '.mov', '.wmv']:
                    self.preview_area.setText("🎥 Fichier vidéo\n\nPrévisualisation non disponible")
                    self.info_label.setText(f"Vidéo: {os.path.basename(file_path)}")
                
                elif file_ext in ['.mp3', '.wav', '.flac', '.aac']:
                    self.preview_area.setText("🎵 Fichier audio\n\nPrévisualisation non disponible")
                    self.info_label.setText(f"Audio: {os.path.basename(file_path)}")
                
                elif file_ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf']:
                    self.preview_area.setText("📄 Document\n\nPrévisualisation non disponible")
                    self.info_label.setText(f"Document: {os.path.basename(file_path)}")
                
                else:
                    self.preview_area.setText("📁 Fichier\n\nType non supporté pour la prévisualisation")
                    self.info_label.setText(f"Fichier: {os.path.basename(file_path)}")
            else:
                self.preview_area.setText("❌ Fichier introuvable")
                self.info_label.setText(f"Le fichier n'existe pas à l'emplacement:\n{file_path}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.db = None
        self.search_history = SearchHistory()
        self.current_search_results = []
        self.init_ui()
        self.load_database()
        self.apply_theme()
    
    def init_ui(self):
        self.setWindowTitle("Gestionnaire de Fichiers avec Tags")
        self.setGeometry(100, 100, 1400, 800)  # Augmenter la largeur
        
        # Widget central et layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)  # Changé en QHBoxLayout
        
        # Splitter principal
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Splitter gauche pour liste et détails
        left_splitter = QSplitter(Qt.Vertical)
        
        # Panel supérieur gauche - Recherche et résultats
        search_panel = QWidget()
        search_layout = QVBoxLayout(search_panel)
        
        # Barre de recherche
        search_bar_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par nom, tag (#tag), collection (@collection)...")
        self.search_input.returnPressed.connect(self.perform_search)
        search_bar_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("Rechercher")
        self.search_button.clicked.connect(self.perform_search)
        search_bar_layout.addWidget(self.search_button)
        
        self.clear_search_button = QPushButton("Effacer")
        self.clear_search_button.clicked.connect(self.clear_search)
        search_bar_layout.addWidget(self.clear_search_button)
        
        search_layout.addLayout(search_bar_layout)
        
        # Liste des résultats
        self.results_list = QListWidget()
        self.results_list.itemSelectionChanged.connect(self.show_object_details)
        self.results_list.itemDoubleClicked.connect(self.open_selected_object)
        search_layout.addWidget(QLabel("Résultats:"))
        search_layout.addWidget(self.results_list)
        
        left_splitter.addWidget(search_panel)
        
        # Panel inférieur gauche - Détails de base
        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        
        # Informations de base
        info_group = QGroupBox("Informations")
        info_layout = QVBoxLayout(info_group)
        
        self.name_label = QLabel("Nom: ")
        self.type_label = QLabel("Type: ")
        self.location_label = QLabel("Emplacement: ")
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.type_label)
        info_layout.addWidget(self.location_label)
        
        details_layout.addWidget(info_group)
        
        # Boutons d'action
        action_layout = QHBoxLayout()
        self.open_button = QPushButton("Ouvrir")
        self.open_button.clicked.connect(self.open_selected_object)
        self.edit_button = QPushButton("Modifier")
        self.edit_button.clicked.connect(self.edit_selected_object)
        self.delete_button = QPushButton("Supprimer")
        self.delete_button.clicked.connect(self.delete_selected_object)
        
        action_layout.addWidget(self.open_button)
        action_layout.addWidget(self.edit_button)
        action_layout.addWidget(self.delete_button)
        details_layout.addLayout(action_layout)
        
        left_splitter.addWidget(details_panel)
        left_splitter.setSizes([400, 200])
        
        main_splitter.addWidget(left_splitter)
        
        # Panel droit - Détails avancés avec onglets
        right_panel = QTabWidget()
        
        # Onglet Description
        desc_tab = QWidget()
        desc_layout = QVBoxLayout(desc_tab)
        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        desc_layout.addWidget(QLabel("Description:"))
        desc_layout.addWidget(self.description_text)
        right_panel.addTab(desc_tab, "Description")
        
        # Onglet Tags
        tags_tab = QWidget()
        tags_layout = QVBoxLayout(tags_tab)
        
        tag_input_layout = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Ajouter un tag...")
        self.tag_input.returnPressed.connect(self.add_tag_to_object)
        tag_input_layout.addWidget(self.tag_input)
        
        self.add_tag_button = QPushButton("Ajouter")
        self.add_tag_button.clicked.connect(self.add_tag_to_object)
        tag_input_layout.addWidget(self.add_tag_button)
        
        tags_layout.addLayout(tag_input_layout)
        
        self.tags_list = QListWidget()
        self.tags_list.itemDoubleClicked.connect(self.remove_tag_from_object)
        tags_layout.addWidget(QLabel("Tags associés:"))
        tags_layout.addWidget(self.tags_list)
        
        right_panel.addTab(tags_tab, "Tags")
        
        # Onglet Collections
        collections_tab = QWidget()
        collections_layout = QVBoxLayout(collections_tab)
        
        collections_action_layout = QHBoxLayout()
        self.manage_collections_button = QPushButton("Gérer les collections")
        self.manage_collections_button.clicked.connect(self.manage_collections)
        collections_action_layout.addWidget(self.manage_collections_button)
        
        self.add_to_collection_button = QPushButton("Ajouter à une collection")
        self.add_to_collection_button.clicked.connect(self.add_to_collection)
        collections_action_layout.addWidget(self.add_to_collection_button)
        
        collections_layout.addLayout(collections_action_layout)
        
        self.collections_list = QListWidget()
        self.collections_list.itemDoubleClicked.connect(self.remove_from_collection)
        collections_layout.addWidget(QLabel("Collections:"))
        collections_layout.addWidget(self.collections_list)
        
        right_panel.addTab(collections_tab, "Collections")
        
        # Onglet Prévisualisation
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        self.preview_widget = PreviewWidget()
        preview_layout.addWidget(self.preview_widget)
        right_panel.addTab(preview_tab, "Prévisualisation")
        
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([600, 800])
        
        main_layout.addWidget(main_splitter)
        
        # Barre de menu
        self.create_menu_bar()
        
        # Barre d'état
        self.statusBar().showMessage("Prêt")
        
        # Contexte menus
        self.setup_context_menus()
        
        # Auto-complétion
        self.setup_autocompletion()
    
    def create_menu_bar(self):
        """Crée la barre de menu"""
        menu_bar = self.menuBar()
        
        # Menu Fichier
        file_menu = menu_bar.addMenu("Fichier")
        
        add_file_action = QAction("Ajouter un fichier", self)
        add_file_action.triggered.connect(self.add_file)
        file_menu.addAction(add_file_action)
        
        bulk_import_action = QAction("Import multiple", self)
        bulk_import_action.triggered.connect(self.bulk_import)
        file_menu.addAction(bulk_import_action)
        
        file_menu.addSeparator()
        
        settings_action = QAction("Paramètres", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Quitter", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Données (NOUVEAU)
        data_menu = menu_bar.addMenu("Données")
        
        tags_action = QAction("Tags", self)
        tags_action.triggered.connect(self.manage_tags)
        data_menu.addAction(tags_action)
        
        collections_action = QAction("Collections", self)
        collections_action.triggered.connect(self.manage_collections)
        data_menu.addAction(collections_action)
        
        # Menu Affichage
        view_menu = menu_bar.addMenu("Affichage")
        
        dark_mode_action = QAction("Mode sombre", self)
        dark_mode_action.setCheckable(True)
        dark_mode_action.setChecked(self.config.get_dark_mode())
        dark_mode_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(dark_mode_action)
        
        # Menu Aide
        help_menu = menu_bar.addMenu("Aide")
        
        about_action = QAction("À propos", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def manage_tags(self):
        """Ouvre la boîte de dialogue de gestion des tags"""
        dialog = TagsDialog(self, self.db)
        dialog.exec_()
        # Rafraîchir l'affichage après la gestion des tags
        self.show_object_details()
        self.update_completion(self.search_input.text())
    
    def manage_classes(self):
        """Ouvre la boîte de dialogue de gestion des classes"""
        dialog = ClassesDialog(self, self.db)
        dialog.exec_()
        # Rafraîchir l'affichage après la gestion des classes
        self.show_object_details()
        self.update_completion(self.search_input.text())

    def setup_autocompletion(self):
        """Configure l'auto-complétion pour la recherche"""
        # Create a QStringListModel for the completer
        self.completion_model = QStringListModel()
        
        self.completer = QCompleter()
        self.completer.setModel(self.completion_model)  # Set the model
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.search_input.setCompleter(self.completer)
        
        # Mettre à jour les suggestions quand le texte change
        self.search_input.textChanged.connect(self.update_completion)
    
    def update_completion(self, text):
        """Met à jour les suggestions d'auto-complétion"""
        if not self.db:
            return
        
        suggestions = []
        
        # Ajouter les tags
        suggestions.extend([f"#{tag}" for tag in self.db.tags.keys()])
        
        # Ajouter les collections
        suggestions.extend([f"@{collection.name}" for collection in self.db.collections.values()])
        
        # Ajouter les opérateurs booléens
        suggestions.extend([" AND ", " OR ", " NOT "])
        
        # Filtrer les suggestions selon le texte actuel
        current_text = text.lower()
        filtered_suggestions = [s for s in suggestions if current_text in s.lower()]
        
        # Mettre à jour le completer
        self.completer.model().setStringList(filtered_suggestions)
    
    def setup_context_menus(self):
        """Configure les menus contextuels"""
        self.results_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_list.customContextMenuRequested.connect(self.show_results_context_menu)
        
        self.tags_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tags_list.customContextMenuRequested.connect(self.show_tags_context_menu)
        
        self.collections_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.collections_list.customContextMenuRequested.connect(self.show_collections_context_menu)

    def show_results_context_menu(self, position):
        """Affiche le menu contextuel pour les résultats"""
        item = self.results_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        
        open_action = QAction("Ouvrir", self)
        open_action.triggered.connect(self.open_selected_object)
        menu.addAction(open_action)
        
        edit_action = QAction("Modifier", self)
        edit_action.triggered.connect(self.edit_selected_object)
        menu.addAction(edit_action)
        
        delete_action = QAction("Supprimer", self)
        delete_action.triggered.connect(self.delete_selected_object)
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        copy_name_action = QAction("Copier le nom", self)
        copy_name_action.triggered.connect(lambda: self.copy_to_clipboard("name"))
        menu.addAction(copy_name_action)
        
        copy_location_action = QAction("Copier l'emplacement", self)
        copy_location_action.triggered.connect(lambda: self.copy_to_clipboard("location"))
        menu.addAction(copy_location_action)
        
        menu.exec_(self.results_list.mapToGlobal(position))
    
    def show_tags_context_menu(self, position):
        """Affiche le menu contextuel pour les tags"""
        item = self.tags_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        
        remove_action = QAction("Retirer le tag", self)
        remove_action.triggered.connect(self.remove_tag_from_object)
        menu.addAction(remove_action)
        
        search_action = QAction("Rechercher ce tag", self)
        search_action.triggered.connect(lambda: self.search_tag(item.text()))
        menu.addAction(search_action)
        
        menu.exec_(self.tags_list.mapToGlobal(position))
    
    def show_collections_context_menu(self, position):
        """Affiche le menu contextuel pour les collections"""
        item = self.collections_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        
        remove_action = QAction("Retirer de la collection", self)
        remove_action.triggered.connect(self.remove_from_collection)
        menu.addAction(remove_action)
        
        view_action = QAction("Voir les objets de la collection", self)
        view_action.triggered.connect(self.view_collection)
        menu.addAction(view_action)
        
        menu.exec_(self.collections_list.mapToGlobal(position))
    
    def copy_to_clipboard(self, what):
        """Copie les informations de l'objet dans le presse-papier"""
        current_item = self.results_list.currentItem()
        if not current_item:
            return
        
        obj_id = current_item.data(Qt.UserRole)
        obj = self.db.objects.get(obj_id)
        if not obj:
            return
        
        clipboard = QApplication.clipboard()
        if what == "name":
            clipboard.setText(obj.name)
        elif what == "location":
            clipboard.setText(obj.location)
    
    def search_tag(self, tag):
        """Recherche les objets avec un tag spécifique"""
        self.search_input.setText(f"#{tag}")
        self.perform_search()
    
    def view_collection(self):
        """Affiche les objets d'une collection"""
        item = self.collections_list.currentItem()
        if not item:
            return
        
        collection_name = item.text()
        self.search_input.setText(f"@{collection_name}")
        self.perform_search()
    
    def load_database(self):
        """Charge la base de données"""
        try:
            data_dir = self.config.get_data_dir()
            self.db = TagDatabase(data_dir)
            self.statusBar().showMessage(f"Base de données chargée: {len(self.db.objects)} objets, {len(self.db.tags)} tags, {len(self.db.collections)} collections")
            
            # Charger l'historique des recherches
            history_file = self.config.get_history_file()
            self.search_history.load_from_file(history_file)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement de la base de données: {e}")
    
    def apply_theme(self):
        """Applique le thème sombre ou clair"""
        if self.config.get_dark_mode():
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
    
    def apply_dark_theme(self):
        """Applique le thème sombre depuis le fichier CSS"""
        theme_file = self.config.get_theme_file()
        if os.path.exists(theme_file):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    style = f.read()
                self.setStyleSheet(style)
            except Exception as e:
                print(f"Erreur lors du chargement du thème: {e}")
                self.apply_default_dark_theme()
        else:
            self.apply_default_dark_theme()
            self.save_default_theme()
    
    def apply_default_dark_theme(self):
        """Applique le thème sombre par défaut"""
        default_dark_theme = """
        QMainWindow, QDialog, QWidget {
            background-color: #2b2b2b;
            color: #ffffff;
            border: none;
        }
        
        QLabel {
            color: #ffffff;
        }
        
        QLineEdit, QTextEdit, QComboBox {
            background-color: #3c3f41;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border: 1px solid #4da6ff;
        }
        
        QPushButton {
            background-color: #4a4a4a;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px 10px;
        }
        
        QPushButton:hover {
            background-color: #5a5a5a;
        }
        
        QPushButton:pressed {
            background-color: #3a3a3a;
        }
        
        QListWidget {
            background-color: #3c3f41;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 3px;
        }
        
        QListWidget::item {
            padding: 5px;
        }
        
        QListWidget::item:selected {
            background-color: #4a4a4a;
        }
        
        QListWidget::item:hover {
            background-color: #5a5a5a;
        }
        
        QTabWidget::pane {
            border: 1px solid #555555;
            background-color: #3c3f41;
        }
        
        QTabBar::tab {
            background-color: #4a4a4a;
            color: #ffffff;
            padding: 8px 12px;
            border-top-left-radius: 3px;
            border-top-right-radius: 3px;
        }
        
        QTabBar::tab:selected {
            background-color: #3c3f41;
            border-bottom: 2px solid #4da6ff;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 1px solid #555555;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 15px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 5px;
        }
        
        QMenuBar {
            background-color: #3c3f41;
            color: #ffffff;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 5px 10px;
        }
        
        QMenuBar::item:selected {
            background-color: #4a4a4a;
        }
        
        QMenu {
            background-color: #3c3f41;
            color: #ffffff;
            border: 1px solid #555555;
        }
        
        QMenu::item:selected {
            background-color: #4a4a4a;
        }
        
        QStatusBar {
            background-color: #3c3f41;
            color: #ffffff;
        }
        
        QScrollBar:vertical {
            background-color: #3c3f41;
            width: 12px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #5a5a5a;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #6a6a6a;
        }
        """
        self.setStyleSheet(default_dark_theme)

    def apply_light_theme(self):
        """Applique le thème clair (style par défaut de Qt)"""
        self.setStyleSheet("")
    
    def save_default_theme(self):
        """Sauvegarde le thème par défaut dans un fichier CSS"""
        theme_file = self.config.get_theme_file()
        default_theme = """/* Theme CSS pour le gestionnaire de fichiers avec tags */
/* Vous pouvez personnaliser ces valeurs selon vos préférences */

QMainWindow, QDialog, QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
    border: none;
}

QLabel {
    color: #ffffff;
}

QLineEdit, QTextEdit, QComboBox {
    background-color: #3c3f41;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 5px;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #4da6ff;
}

QPushButton {
    background-color: #4a4a4a;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 5px 10px;
}

QPushButton:hover {
    background-color: #5a5a5a;
}

QPushButton:pressed {
    background-color: #3a3a3a;
}

QListWidget {
    background-color: #3c3f41;
    color: #ffffff;
    border: 1px solid #555555;
    border-radius: 3px;
}

QListWidget::item {
    padding: 5px;
}

QListWidget::item:selected {
    background-color: #4a4a4a;
}

QListWidget::item:hover {
    background-color: #5a5a5a;
}

QTabWidget::pane {
    border: 1px solid #555555;
    background-color: #3c3f41;
}

QTabBar::tab {
    background-color: #4a4a4a;
    color: #ffffff;
    padding: 8px 12px;
    border-top-left-radius: 3px;
    border-top-right-radius: 3px;
}

QTabBar::tab:selected {
    background-color: #3c3f41;
    border-bottom: 2px solid #4da6ff;
}

QGroupBox {
    font-weight: bold;
    border: 1px solid #555555;
    border-radius: 5px;
    margin-top: 10px;
    padding-top: 15px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 5px;
}

QMenuBar {
    background-color: #3c3f41;
    color: #ffffff;
}

QMenuBar::item {
    background-color: transparent;
    padding: 5px 10px;
}

QMenuBar::item:selected {
    background-color: #4a4a4a;
}

QMenu {
    background-color: #3c3f41;
    color: #ffffff;
    border: 1px solid #555555;
}

QMenu::item:selected {
    background-color: #4a4a4a;
}

QStatusBar {
    background-color: #3c3f41;
    color: #ffffff;
}

QScrollBar:vertical {
    background-color: #3c3f41;
    width: 12px;
}

QScrollBar::handle:vertical {
    background-color: #5a5a5a;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background-color: #6a6a6a;
}

/* Personnalisation supplémentaire */
#preview_area {
    border: 2px dashed #666666;
    background-color: #2b2b2b;
    border-radius: 5px;
}

#search_input {
    font-size: 14px;
}

#results_list {
    font-family: "Segoe UI", Arial, sans-serif;
}
"""
        try:
            with open(theme_file, 'w', encoding='utf-8') as f:
                f.write(default_theme)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du thème: {e}")

    def toggle_dark_mode(self):
        """Bascule entre le mode sombre et le mode clair"""
        current = self.config.get_dark_mode()
        self.config.set_dark_mode(not current)
        self.apply_theme()
    
    def perform_search(self):
        """Effectue une recherche"""
        query = self.search_input.text().strip()
        if not query:
            self.clear_search()
            return
        
        # Ajouter à l'historique
        self.search_history.add_search(query)
        
        # Sauvegarder l'historique
        history_file = self.config.get_history_file()
        self.search_history.save_to_file(history_file)
        
        # Effectuer la recherche
        results = self.db.advanced_search(query)
        self.current_search_results = results
        
        # Afficher les résultats
        self.results_list.clear()
        for obj in results:
            item = QListWidgetItem(f"{obj.name} ({obj.file_type})")
            item.setData(Qt.UserRole, obj.id)
            self.results_list.addItem(item)
        
        # Mettre à jour la barre d'état
        self.statusBar().showMessage(f"{len(results)} résultat(s) trouvé(s) pour: {query}")
        
        # Effacer les détails
        self.clear_object_details()
    
    def clear_search(self):
        """Efface la recherche et affiche tous les objets"""
        self.search_input.clear()
        self.current_search_results = list(self.db.objects.values())
        self.results_list.clear()
        for obj in self.current_search_results:
            item = QListWidgetItem(f"{obj.name} ({obj.file_type})")
            item.setData(Qt.UserRole, obj.id)
            self.results_list.addItem(item)
        
        self.statusBar().showMessage(f"Affichage de tous les objets: {len(self.current_search_results)}")
        self.clear_object_details()
    
    def show_object_details(self):
        """Affiche les détails de l'objet sélectionné"""
        current_item = self.results_list.currentItem()
        if not current_item:
            self.clear_object_details()
            return
        
        obj_id = current_item.data(Qt.UserRole)
        obj = self.db.objects.get(obj_id)
        if not obj:
            self.clear_object_details()
            return
        
        # Afficher les informations de base
        self.name_label.setText(f"Nom: {obj.name}")
        self.type_label.setText(f"Type: {obj.file_type}")
        location_text = f"Emplacement: {obj.location}"
        if obj.is_external():
            location_text += " 🌐"
        else:
            location_text += " 💾"
        self.location_label.setText(location_text)
        
        # Afficher la description
        self.description_text.setPlainText(obj.description)
        
        # Afficher les tags
        self.tags_list.clear()
        tags = self.db.get_object_tags(obj_id)
        for tag in tags:
            self.tags_list.addItem(tag)
        
        # Afficher les collections
        self.collections_list.clear()
        collections = self.db.get_collections_for_object(obj_id)
        for collection in collections:
            self.collections_list.addItem(collection.name)
        
        # Afficher la prévisualisation
        self.preview_widget.set_preview(obj)
    
    def clear_object_details(self):
        """Efface les détails de l'objet"""
        self.name_label.setText("Nom: ")
        self.type_label.setText("Type: ")
        self.location_label.setText("Emplacement: ")
        self.description_text.clear()
        self.tags_list.clear()
        self.collections_list.clear()
        self.preview_widget.clear_preview()  # Effacer la prévisualisation
    
    def add_tag_to_object(self):
        """Ajoute un tag à l'objet sélectionné"""
        current_item = self.results_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Erreur", "Aucun objet sélectionné.")
            return
        
        tag = self.tag_input.text().strip()
        if not tag:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un tag.")
            return
        
        obj_id = current_item.data(Qt.UserRole)
        self.db.add_tag(obj_id, tag)
        self.show_object_details()  # Rafraîchir l'affichage
        self.tag_input.clear()
        
        # Mettre à jour l'auto-complétion
        self.update_completion(self.search_input.text())
    
    def remove_tag_from_object(self):
        """Retire un tag de l'objet sélectionné"""
        current_item = self.tags_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Erreur", "Aucun tag sélectionné.")
            return
        
        obj_item = self.results_list.currentItem()
        if not obj_item:
            return
        
        tag = current_item.text()
        obj_id = obj_item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir retirer le tag '{tag}' ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.db.remove_tag(obj_id, tag)
            self.show_object_details()  # Rafraîchir l'affichage
    
    def add_to_collection(self):
        """Ajoute l'objet sélectionné à une collection"""
        current_item = self.results_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Erreur", "Aucun objet sélectionné.")
            return
        
        obj_id = current_item.data(Qt.UserRole)
        
        # Demander à l'utilisateur de choisir une collection
        collections = list(self.db.collections.values())
        if not collections:
            QMessageBox.information(self, "Information", "Aucune collection disponible. Veuillez d'abord créer une collection.")
            self.manage_collections()
            return
        
        collection_names = [collection.name for collection in collections]
        collection_name, ok = QInputDialog.getItem(
            self,
            "Ajouter à une collection",
            "Choisissez une collection:",
            collection_names,
            0,
            False
        )
        
        if ok and collection_name:
            # Trouver la collection correspondante
            for collection in collections:
                if collection.name == collection_name:
                    success = self.db.add_object_to_collection(obj_id, collection.id)
                    if success:
                        QMessageBox.information(self, "Succès", f"Objet ajouté à la collection '{collection_name}'.")
                        self.show_object_details()  # Rafraîchir l'affichage
                    else:
                        QMessageBox.warning(self, "Erreur", "Impossible d'ajouter l'objet à la collection.")
                    break
    
    def remove_from_collection(self):
        """Retire l'objet sélectionné d'une collection"""
        current_collection_item = self.collections_list.currentItem()
        if not current_collection_item:
            QMessageBox.warning(self, "Erreur", "Aucune collection sélectionnée.")
            return
        
        current_obj_item = self.results_list.currentItem()
        if not current_obj_item:
            return
        
        collection_name = current_collection_item.text()
        obj_id = current_obj_item.data(Qt.UserRole)
        
        # Trouver la collection correspondante
        collection = None
        for col in self.db.collections.values():
            if col.name == collection_name:
                collection = col
                break
        
        if not collection:
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir retirer cet objet de la collection '{collection_name}' ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.db.remove_object_from_collection(obj_id, collection.id)
            if success:
                QMessageBox.information(self, "Succès", f"Objet retiré de la collection '{collection_name}'.")
                self.show_object_details()  # Rafraîchir l'affichage
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de retirer l'objet de la collection.")
    
    def manage_collections(self):
        """Ouvre la boîte de dialogue de gestion des collections"""
        dialog = CollectionsDialog(self, self.db)
        dialog.exec_()
        # Rafraîchir l'affichage après la gestion des collections
        self.show_object_details()
        self.update_completion(self.search_input.text())
    
    def open_selected_object(self):
        """Ouvre l'objet sélectionné"""
        current_item = self.results_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Erreur", "Aucun objet sélectionné.")
            return
        
        obj_id = current_item.data(Qt.UserRole)
        obj = self.db.objects.get(obj_id)
        if not obj:
            QMessageBox.warning(self, "Erreur", "Objet introuvable.")
            return
        
        success = obj.open_location()
        if not success:
            QMessageBox.warning(self, "Erreur", "Impossible d'ouvrir l'emplacement.")
    
    def edit_selected_object(self):
        """Modifie l'objet sélectionné"""
        current_item = self.results_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Erreur", "Aucun objet sélectionné.")
            return
        
        obj_id = current_item.data(Qt.UserRole)
        obj = self.db.objects.get(obj_id)
        if not obj:
            QMessageBox.warning(self, "Erreur", "Objet introuvable.")
            return
        
        # Ouvrir la boîte de dialogue d'édition
        dialog = AddFileDialog(self, self.db, obj)
        if dialog.exec() == QDialog.Accepted:
            # L'objet a été modifié, rafraîchir l'affichage
            self.perform_search()  # Rafraîchir la recherche pour voir les modifications
            self.show_object_details()
    
    def delete_selected_object(self):
        """Supprime l'objet sélectionné"""
        current_item = self.results_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Erreur", "Aucun objet sélectionné.")
            return
        
        obj_id = current_item.data(Qt.UserRole)
        obj = self.db.objects.get(obj_id)
        if not obj:
            QMessageBox.warning(self, "Erreur", "Objet introuvable.")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer '{obj.name}' ?\nCette action est irréversible.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.db.delete_object(obj_id)
            if success:
                QMessageBox.information(self, "Succès", "Objet supprimé avec succès.")
                self.perform_search()  # Rafraîchir la liste
                self.clear_object_details()
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de supprimer l'objet.")
    
    def add_file(self):
        """Ouvre la boîte de dialogue pour ajouter un fichier"""
        dialog = AddFileDialog(self, self.db)
        if dialog.exec() == QDialog.Accepted:
            # Rafraîchir l'affichage
            self.clear_search()
    
    def bulk_import(self):
        """Importe plusieurs fichiers en une fois"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Sélectionner les fichiers à importer",
            "",
            "Tous les fichiers (*)"
        )
        
        if not files:
            return
        
        progress = QProgressDialog("Importation en cours...", "Annuler", 0, len(files), self)
        progress.setWindowModality(Qt.WindowModal)
        
        success_count = 0
        duplicate_count = 0
        error_count = 0
        
        for i, file_path in enumerate(files):
            progress.setValue(i)
            if progress.wasCanceled():
                break
            
            try:
                file_name = os.path.basename(file_path)
                file_type = self.detect_file_type(file_path)
                
                # Vérifier si le fichier existe déjà
                if self.db.location_exists(file_path):
                    duplicate_count += 1
                    continue
                
                obj = FileObject(file_name, "", file_type, file_path)
                obj_id = self.db.add_object(obj)
                
                if obj_id:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"Erreur lors de l'import de {file_path}: {e}")
        
        progress.setValue(len(files))
        
        # Afficher le rapport
        QMessageBox.information(
            self,
            "Importation terminée",
            f"Importation terminée:\n"
            f"- {success_count} fichiers importés avec succès\n"
            f"- {duplicate_count} fichiers déjà existants\n"
            f"- {error_count} erreurs"
        )
        
        # Rafraîchir l'affichage
        self.clear_search()
    
    def detect_file_type(self, file_path: str) -> str:
        """Détecte le type de fichier basé sur l'extension"""
        ext = os.path.splitext(file_path)[1].lower()
        
        image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        video_exts = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm']
        audio_exts = ['.mp3', '.wav', '.ogg', '.flac', '.aac', '.wma']
        doc_exts = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx']
        
        if ext in image_exts:
            return "image"
        elif ext in video_exts:
            return "video"
        elif ext in audio_exts:
            return "audio"
        elif ext in doc_exts:
            return "document"
        else:
            return "autre"
    
    def show_settings(self):
        """Affiche les paramètres"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Paramètres")
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        # Dossier de données
        data_layout = QHBoxLayout()
        data_layout.addWidget(QLabel("Dossier de données:"))
        self.data_dir_input = QLineEdit(self.config.get_data_dir())
        data_layout.addWidget(self.data_dir_input)
        
        browse_button = QPushButton("Parcourir...")
        browse_button.clicked.connect(self.browse_data_dir)
        data_layout.addWidget(browse_button)
        
        layout.addLayout(data_layout)
        
        # Mode sombre
        dark_mode_checkbox = QCheckBox("Mode sombre")
        dark_mode_checkbox.setChecked(self.config.get_dark_mode())
        dark_mode_checkbox.stateChanged.connect(lambda state: self.config.set_dark_mode(state == Qt.Checked))
        layout.addWidget(dark_mode_checkbox)
        
        # Boutons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(dialog.reject)
        save_button = QPushButton("Sauvegarder")
        save_button.clicked.connect(lambda: self.save_settings(dialog))
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def browse_data_dir(self):
        """Ouvre une boîte de dialogue pour choisir le dossier de données"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier de données",
            self.config.get_data_dir()
        )
        
        if directory:
            self.data_dir_input.setText(directory)
    
    def save_settings(self, dialog):
        """Sauvegarde les paramètres"""
        data_dir = self.data_dir_input.text().strip()
        if data_dir:
            self.config.set_data_dir(data_dir)
            dialog.accept()
            
            # Recharger la base de données avec le nouveau dossier
            self.load_database()
            self.clear_search()
    
    def show_about(self):
        """Affiche la boîte de dialogue À propos"""
        QMessageBox.about(
            self,
            "À propos",
            "Gestionnaire de Fichiers avec Tags\n\n"
            "Une application pour organiser et rechercher vos fichiers avec des tags.\n\n"
            "Fonctionnalités:\n"
            "- Ajout et gestion de fichiers avec tags\n"
            "- Recherche avancée avec syntaxe booléenne\n"
            "- Gestion des collections d'objets\n"
            "- Interface intuitive avec mode sombre\n"
            "- Support des fichiers locaux et URLs web"
        )

class TagsDialog(QDialog):
    """Boîte de dialogue pour afficher la liste des tags et leur utilisation"""
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Gestion des Tags")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.init_ui()
        self.load_tags()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Barre de recherche
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Rechercher:"))
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_tags)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Liste des tags
        self.tags_list = QListWidget()
        self.tags_list.itemDoubleClicked.connect(self.search_tag)
        layout.addWidget(QLabel("Tags:"))
        layout.addWidget(self.tags_list)
        
        # Informations sur le tag sélectionné
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # Boutons
        button_layout = QHBoxLayout()
        self.search_button = QPushButton("Rechercher ce tag")
        self.search_button.clicked.connect(self.search_selected_tag)
        self.delete_button = QPushButton("Supprimer le tag")
        self.delete_button.clicked.connect(self.delete_selected_tag)
        
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)
        
        # Bouton de fermeture
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.update_buttons()
    
    def load_tags(self):
        """Charge la liste des tags"""
        self.all_tags = []
        self.tags_list.clear()
        
        if not self.db:
            return
        
        # Trier les tags par nombre d'objets (décroissant)
        sorted_tags = sorted(self.db.tags.items(), key=lambda x: len(x[1]), reverse=True)
        
        for tag, obj_ids in sorted_tags:
            count = len(obj_ids)
            item = QListWidgetItem(f"{tag} ({count} objet{'s' if count > 1 else ''})")
            item.setData(Qt.UserRole, tag)
            self.tags_list.addItem(item)
            self.all_tags.append((tag, count))
    
    def filter_tags(self, text):
        """Filtre les tags selon le texte de recherche"""
        self.tags_list.clear()
        search_text = text.lower()
        
        for tag, count in self.all_tags:
            if search_text in tag.lower():
                item = QListWidgetItem(f"{tag} ({count} objet{'s' if count > 1 else ''})")
                item.setData(Qt.UserRole, tag)
                self.tags_list.addItem(item)
    
    def update_buttons(self):
        """Met à jour l'état des boutons selon la sélection"""
        has_selection = self.tags_list.currentItem() is not None
        self.search_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        
        # Afficher les informations du tag sélectionné
        if has_selection:
            tag = self.tags_list.currentItem().data(Qt.UserRole)
            count = len(self.db.tags.get(tag, []))
            self.info_label.setText(f"Tag: #{tag}\nUtilisé par {count} objet{'s' if count > 1 else ''}")
        else:
            self.info_label.clear()
    
    def search_selected_tag(self):
        """Lance une recherche avec le tag sélectionné"""
        item = self.tags_list.currentItem()
        if item:
            self.search_tag(item)
    
    def search_tag(self, item):
        """Recherche les objets avec le tag sélectionné"""
        tag = item.data(Qt.UserRole)
        self.parent().search_input.setText(f"#{tag}")
        self.parent().perform_search()
        self.accept()
    
    def delete_selected_tag(self):
        """Supprime le tag sélectionné de tous les objets"""
        item = self.tags_list.currentItem()
        if not item:
            return
        
        tag = item.data(Qt.UserRole)
        count = len(self.db.tags.get(tag, []))
        
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer le tag '{tag}' ?\n"
            f"Il sera retiré de {count} objet{'s' if count > 1 else ''}.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Retirer le tag de tous les objets
            for obj_id in list(self.db.tags.get(tag, [])):
                self.db.remove_tag(obj_id, tag)
            
            # Supprimer le fichier de tag
            tag_file = self.db.tag_files.get(tag)
            if tag_file and os.path.exists(tag_file):
                try:
                    os.remove(tag_file)
                except Exception as e:
                    print(f"Erreur lors de la suppression du fichier {tag_file}: {e}")
            
            # Mettre à jour les structures de données
            if tag in self.db.tags:
                del self.db.tags[tag]
            if tag in self.db.tag_files:
                del self.db.tag_files[tag]
            
            QMessageBox.information(self, "Succès", f"Tag '{tag}' supprimé avec succès.")
            self.load_tags()

class ClassesDialog(QDialog):
    """Boîte de dialogue pour afficher la liste des classes et leur utilisation"""
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Gestion des Classes")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.init_ui()
        self.load_classes()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Information
        info_label = QLabel("Les classes fonctionnent comme des tags mais sont utilisées pour une classification hiérarchique.")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("background-color: #f0f0f0; padding: 5px; border-radius: 3px;")
        layout.addWidget(info_label)
        
        # Barre de recherche
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Rechercher:"))
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self.filter_classes)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Liste des classes
        self.classes_list = QListWidget()
        self.classes_list.itemDoubleClicked.connect(self.search_class)
        layout.addWidget(QLabel("Collection:"))
        layout.addWidget(self.classes_list)
        
        # Informations sur la classe sélectionnée
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # Boutons
        button_layout = QHBoxLayout()
        self.search_button = QPushButton("Rechercher cette classe")
        self.search_button.clicked.connect(self.search_selected_class)
        self.delete_button = QPushButton("Supprimer la classe")
        self.delete_button.clicked.connect(self.delete_selected_class)
        
        button_layout.addWidget(self.search_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)
        
        # Bouton de fermeture
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.update_buttons()
    
    def load_classes(self):
        """Charge la liste des classes"""
        self.all_classes = []
        self.classes_list.clear()
        
        if not self.db:
            return
        
        # Pour cet exemple, nous utilisons les tags qui commencent par "class:"
        # comme système de classes
        class_prefix = "class:"
        class_tags = {}
        
        for tag, obj_ids in self.db.tags.items():
            if tag.startswith(class_prefix):
                class_name = tag[len(class_prefix):]
                class_tags[class_name] = len(obj_ids)
        
        # Trier les classes par nombre d'objets (décroissant)
        sorted_classes = sorted(class_tags.items(), key=lambda x: x[1], reverse=True)
        
        for class_name, count in sorted_classes:
            item = QListWidgetItem(f"{class_name} ({count} objet{'s' if count > 1 else ''})")
            item.setData(Qt.UserRole, class_name)
            self.classes_list.addItem(item)
            self.all_classes.append((class_name, count))
    
    def filter_classes(self, text):
        """Filtre les classes selon le texte de recherche"""
        self.classes_list.clear()
        search_text = text.lower()
        
        for class_name, count in self.all_classes:
            if search_text in class_name.lower():
                item = QListWidgetItem(f"{class_name} ({count} objet{'s' if count > 1 else ''})")
                item.setData(Qt.UserRole, class_name)
                self.classes_list.addItem(item)
    
    def update_buttons(self):
        """Met à jour l'état des boutons selon la sélection"""
        has_selection = self.classes_list.currentItem() is not None
        self.search_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        
        # Afficher les informations de la classe sélectionnée
        if has_selection:
            class_name = self.classes_list.currentItem().data(Qt.UserRole)
            tag_name = f"class:{class_name}"
            count = len(self.db.tags.get(tag_name, []))
            self.info_label.setText(f"Classe: {class_name}\nUtilisée par {count} objet{'s' if count > 1 else ''}")
        else:
            self.info_label.clear()
    
    def search_selected_class(self):
        """Lance une recherche avec la classe sélectionnée"""
        item = self.classes_list.currentItem()
        if item:
            self.search_class(item)
    
    def search_class(self, item):
        """Recherche les objets avec la classe sélectionnée"""
        class_name = item.data(Qt.UserRole)
        self.parent().search_input.setText(f"#class:{class_name}")
        self.parent().perform_search()
        self.accept()
    
    def delete_selected_class(self):
        """Supprime la classe sélectionnée de tous les objets"""
        item = self.classes_list.currentItem()
        if not item:
            return
        
        class_name = item.data(Qt.UserRole)
        tag_name = f"class:{class_name}"
        count = len(self.db.tags.get(tag_name, []))
        
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer la classe '{class_name}' ?\n"
            f"Il sera retiré de {count} objet{'s' if count > 1 else ''}.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Retirer la classe de tous les objets
            for obj_id in list(self.db.tags.get(tag_name, [])):
                self.db.remove_tag(obj_id, tag_name)
            
            # Supprimer le fichier de tag
            tag_file = self.db.tag_files.get(tag_name)
            if tag_file and os.path.exists(tag_file):
                try:
                    os.remove(tag_file)
                except Exception as e:
                    print(f"Erreur lors de la suppression du fichier {tag_file}: {e}")
            
            # Mettre à jour les structures de données
            if tag_name in self.db.tags:
                del self.db.tags[tag_name]
            if tag_name in self.db.tag_files:
                del self.db.tag_files[tag_name]
            
            QMessageBox.information(self, "Succès", f"Classe '{class_name}' supprimée avec succès.")
            self.load_classes()

class AddFileDialog(QDialog):
    def __init__(self, parent=None, db=None, edit_object=None):
        super().__init__(parent)
        self.db = db
        self.edit_object = edit_object
        
        if edit_object:
            self.setWindowTitle("Modifier le fichier")
            self.is_edit = True
        else:
            self.setWindowTitle("Ajouter un fichier")
            self.is_edit = False
            
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Nom
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nom:"))
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["image", "video", "audio", "document", "autre"])
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Emplacement
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Emplacement:"))
        self.location_input = QLineEdit()
        location_layout.addWidget(self.location_input)
        
        browse_button = QPushButton("Parcourir...")
        browse_button.clicked.connect(self.browse_file)
        location_layout.addWidget(browse_button)
        
        layout.addLayout(location_layout)
        
        # Description
        desc_layout = QVBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(100)
        desc_layout.addWidget(self.desc_input)
        layout.addLayout(desc_layout)
        
        # Tags initiaux
        tags_layout = QHBoxLayout()
        tags_layout.addWidget(QLabel("Tags (séparés par des virgules):"))
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("tag1, tag2, tag3...")
        tags_layout.addWidget(self.tags_input)
        layout.addLayout(tags_layout)
        
        # Remplir les champs si on est en mode édition
        if self.is_edit and self.edit_object:
            self.name_input.setText(self.edit_object.name)
            self.type_combo.setCurrentText(self.edit_object.file_type)
            self.location_input.setText(self.edit_object.location)
            self.desc_input.setPlainText(self.edit_object.description)
            
            # Charger les tags existants
            tags = self.db.get_object_tags(self.edit_object.id)
            self.tags_input.setText(", ".join(tags))
        
        # Boutons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(self.reject)
        save_button = QPushButton("Sauvegarder")
        save_button.clicked.connect(self.save_file)
        
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        layout.addLayout(button_layout)
    
    def browse_file(self):
        """Ouvre une boîte de dialogue pour choisir un fichier"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier",
            "",
            "Tous les fichiers (*)"
        )
        
        if file_path:
            self.location_input.setText(file_path)
            # Déduire le nom du fichier si le champ nom est vide
            if not self.name_input.text().strip():
                file_name = os.path.basename(file_path)
                self.name_input.setText(file_name)
    
    def save_file(self):
        """Sauvegarde le fichier"""
        name = self.name_input.text().strip()
        file_type = self.type_combo.currentText()
        location = self.location_input.text().strip()
        description = self.desc_input.toPlainText().strip()
        tags = [tag.strip() for tag in self.tags_input.text().split(',') if tag.strip()]
        
        # Validation
        if not name:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un nom.")
            return
        
        if not location:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un emplacement.")
            return
        
        if self.is_edit:
            # Mode édition
            success = self.db.update_object(
                self.edit_object.id, name, description, file_type, location
            )
            
            if not success:
                QMessageBox.warning(self, "Erreur", "Cet emplacement est déjà utilisé par un autre objet.")
                return
            
            # Mettre à jour les tags
            current_tags = set(self.db.get_object_tags(self.edit_object.id))
            new_tags = set(tags)
            
            # Ajouter les nouveaux tags
            for tag in new_tags - current_tags:
                self.db.add_tag(self.edit_object.id, tag)
            
            # Supprimer les tags retirés
            for tag in current_tags - new_tags:
                self.db.remove_tag(self.edit_object.id, tag)
            
            QMessageBox.information(self, "Succès", "Fichier modifié avec succès.")
            
        else:
            # Mode ajout
            # Vérifier si l'emplacement existe déjà
            if self.db.location_exists(location):
                QMessageBox.warning(self, "Erreur", "Cet emplacement est déjà utilisé.")
                return
            
            obj = FileObject(name, description, file_type, location)
            obj_id = self.db.add_object(obj)
            
            if obj_id:
                # Ajouter les tags
                for tag in tags:
                    self.db.add_tag(obj_id, tag)
                
                QMessageBox.information(self, "Succès", "Fichier ajouté avec succès.")
            else:
                QMessageBox.warning(self, "Erreur", "Erreur lors de l'ajout du fichier.")
                return
        
        self.accept()

def main():
    app = QApplication([])
    
    # Vérifier le premier démarrage
    config = Config()
    if config.is_first_run():
        # Créer le dossier de données par défaut
        data_dir = config.get_data_dir()
        os.makedirs(data_dir, exist_ok=True)
        config.set_first_run_complete()
    
    window = MainWindow()
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()