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
from PyQt5.QtCore import Qt, QUrl, QSettings
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
        self.objects: Dict[str, FileObject] = {}  # ID -> FileObject
        self.tags: Dict[str, Set[str]] = {}       # Tag -> Set d'IDs
        self.tag_files: Dict[str, str] = {}       # Tag -> Chemin du fichier
        
        # Créer les répertoires de données s'ils n'existent pas
        os.makedirs(self.objects_dir, exist_ok=True)
        os.makedirs(self.tags_dir, exist_ok=True)
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
            # Debug: afficher la requête parsée
            parsed_query = self.parse_boolean_query(query)
            print(f"Requête parsée: {parsed_query}")
            
            # Évaluer la requête
            result_ids = self.evaluate_boolean_expression(parsed_query)
            
            # Convertir les IDs en objets
            results = []
            for obj_id in result_ids:
                if obj_id in self.objects:
                    results.append(self.objects[obj_id])
            
            print(f"Résultats trouvés: {len(results)}")
            return results
            
        except Exception as e:
            print(f"Erreur dans la recherche avancée: {e}")
            import traceback
            traceback.print_exc()
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

class ImportFolderDialog(QDialog):
    """Boîte de dialogue pour l'import de dossier avec options"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Importer un dossier")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Type de fichier par défaut
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type de fichier par défaut:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["image", "video", "audio", "document", "autre"])
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Tags
        tags_layout = QVBoxLayout()
        tags_layout.addWidget(QLabel("Tags à appliquer (optionnel):"))
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Exemple: vacances été 2024")
        tags_layout.addWidget(self.tags_input)
        tags_layout.addWidget(QLabel("Séparez les tags par des espaces, virgules ou points-virgules"))
        layout.addLayout(tags_layout)
        
        # Options avancées
        advanced_group = QGroupBox("Options avancées")
        advanced_layout = QVBoxLayout()
        
        self.recursive_check = QCheckBox("Importer les sous-dossiers récursivement")
        self.recursive_check.setChecked(True)
        self.recursive_check.setToolTip("Recherche les fichiers dans tous les sous-dossiers")
        advanced_layout.addWidget(self.recursive_check)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # Boutons
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        self.import_button = QPushButton("Importer")
        self.import_button.clicked.connect(self.accept)
        self.import_button.setDefault(True)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.import_button)
        layout.addLayout(button_layout)
    
    def get_data(self):
        """Retourne les données saisies"""
        tags = self.parse_tags(self.tags_input.text())
        
        return {
            "file_type": self.type_combo.currentText(),
            "tags": tags,
            "recursive": self.recursive_check.isChecked()
        }
    
    def parse_tags(self, tags_input: str) -> List[str]:
        """Parse une chaîne de tags en liste de tags nettoyés"""
        if not tags_input.strip():
            return []
        
        # Séparer par espaces, virgules, points-virgules
        raw_tags = re.split(r'[,\s;]+', tags_input.strip())
        cleaned_tags = []
        for tag in raw_tags:
            cleaned_tag = tag.strip().lstrip('#')
            if cleaned_tag:
                cleaned_tags.append(cleaned_tag)
        
        return cleaned_tags

class FirstRunDialog(QDialog):
    """Boîte de dialogue pour le premier démarrage"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration initiale")
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Bienvenue dans le Gestionnaire de Fichiers par Tags!"))
        layout.addWidget(QLabel("Veuillez choisir un emplacement pour stocker vos données:"))
        
        # Sélection du dossier
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Dossier de données:"))
        self.folder_input = QLineEdit()
        self.folder_input.setText(os.path.join(os.path.expanduser("~"), "TagManagerData"))
        folder_layout.addWidget(self.folder_input)
        
        self.browse_button = QPushButton("Parcourir...")
        self.browse_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.browse_button)
        
        layout.addLayout(folder_layout)
        
        # Boutons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
    
    def browse_folder(self):
        """Ouvre une boîte de dialogue pour sélectionner un dossier"""
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier de données")
        if folder:
            self.folder_input.setText(folder)
    
    def get_data_dir(self):
        """Retourne le dossier de données choisi"""
        return self.folder_input.text()

class FileDialog(QDialog):
    """Boîte de dialogue pour ajouter ou modifier un fichier"""
    def __init__(self, parent=None, obj=None):
        super().__init__(parent)
        self.obj = obj
        if obj:
            self.setWindowTitle("Modifier le fichier")
            self.is_edit = True
        else:
            self.setWindowTitle("Ajouter un nouveau fichier")
            self.is_edit = False
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Champs de formulaire
        form_layout = QVBoxLayout()
        
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nom:"))
        self.name_input = QLineEdit()
        name_layout.addWidget(self.name_input)
        
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["image", "video", "audio", "document", "autre"])
        type_layout.addWidget(self.type_combo)
        
        # Sélection du type d'emplacement
        location_type_layout = QHBoxLayout()
        location_type_layout.addWidget(QLabel("Type d'emplacement:"))
        self.location_type_combo = QComboBox()
        self.location_type_combo.addItems(["Interne (fichier local)", "Externe (URL web)"])
        self.location_type_combo.currentTextChanged.connect(self.update_location_field)
        location_type_layout.addWidget(self.location_type_combo)
        
        # Champ pour l'emplacement (sera mis à jour selon le type)
        self.location_layout = QHBoxLayout()
        self.location_layout.addWidget(QLabel("Emplacement:"))
        self.location_input = QLineEdit()
        self.location_layout.addWidget(self.location_input)
        
        # Bouton pour parcourir les fichiers locaux
        self.browse_button = QPushButton("Parcourir...")
        self.browse_button.clicked.connect(self.browse_file)
        self.location_layout.addWidget(self.browse_button)
        
        description_layout = QVBoxLayout()
        description_layout.addWidget(QLabel("Description:"))
        self.description_input = QTextEdit()
        description_layout.addWidget(self.description_input)
        
        form_layout.addLayout(name_layout)
        form_layout.addLayout(type_layout)
        form_layout.addLayout(location_type_layout)
        form_layout.addLayout(self.location_layout)
        form_layout.addLayout(description_layout)
        
        # Boutons
        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
        # Remplir les champs si on est en mode édition
        if self.is_edit and self.obj:
            self.name_input.setText(self.obj.name)
            self.description_input.setPlainText(self.obj.description)
            self.type_combo.setCurrentText(self.obj.file_type)
            
            if self.obj.is_external():
                self.location_type_combo.setCurrentText("Externe (URL web)")
            else:
                self.location_type_combo.setCurrentText("Interne (fichier local)")
            
            self.location_input.setText(self.obj.location)
        
        # Initialiser l'interface
        self.update_location_field()
    
    def update_location_field(self):
        """Met à jour le champ d'emplacement selon le type sélectionné"""
        location_type = self.location_type_combo.currentText()
        if location_type == "Interne (fichier local)":
            self.location_input.setPlaceholderText("Chemin du fichier local...")
            self.browse_button.setVisible(True)
        else:
            self.location_input.setPlaceholderText("URL (http://, https://)...")
            self.browse_button.setVisible(False)
    
    def browse_file(self):
        """Ouvre une boîte de dialogue pour sélectionner un fichier local"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier")
        if file_path:
            self.location_input.setText(file_path)
    
    def get_data(self):
        """Retourne les données saisies"""
        return {
            "name": self.name_input.text(),
            "description": self.description_input.toPlainText(),
            "type": self.type_combo.currentText(),
            "location": self.location_input.text()
        }

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
            self.preview_area.setText("🌐 Lien externe\n\nCliquez sur 'Ouvrir l'emplacement' pour visiter le site")
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

class SearchHelpDialog(QDialog):
    """Boîte de dialogue d'aide pour la syntaxe de recherche"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Aide sur la syntaxe de recherche")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h2>Syntaxe de recherche avancée</h2>
        
        <h3>Opérateurs booléens:</h3>
        <ul>
            <li><b>AND</b> - Intersection: <code>chat AND chien</code></li>
            <li><b>OR</b> - Union: <code>chat OR chien</code></li>
            <li><b>NOT</b> - Exclusion: <code>chat NOT chien</code></li>
        </ul>
        
        <h3>Priorité des opérateurs:</h3>
        <ul>
            <li>NOT > AND > OR</li>
            <li>Utilisez les parenthèses pour changer la priorité: <code>(chat OR chien) AND animal</code></li>
        </ul>
        
        <h3>Recherche par tags:</h3>
        <ul>
            <li>Utilisez <code>#</code> pour les tags: <code>#vacances #été</code></li>
            <li>Combine avec les opérateurs: <code>#vacances AND #plage</code></li>
        </ul>
        
        <h3>Recherche exacte:</h3>
        <ul>
            <li>Utilisez les guillemets pour la recherche exacte: <code>"mon document.txt"</code></li>
        </ul>
        
        <h3>Wildcards:</h3>
        <ul>
            <li><code>*</code> - Zéro ou plusieurs caractères: <code>photo*.jpg</code></li>
            <li><code>?</code> - Un caractère: <code>image?.png</code></li>
        </ul>
        
        <h3>Exemples:</h3>
        <ul>
            <li><code>#vacances AND (photo OR vidéo)</code></li>
            <li><code>document*.pdf NOT #archives</code></li>
            <li><code>#travail AND (#important OR #urgent)</code></li>
        </ul>
        """)
        
        layout.addWidget(help_text)
        
        # Bouton de fermeture
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.db = None
        self.current_object = None
        self.search_history = SearchHistory()
        self.init_ui()
        self.load_database()
        self.apply_theme()
        self.load_search_history()  # Charger l'historique au démarrage
    
    def load_search_history(self):
        """Charge l'historique des recherches"""
        history_file = self.config.get_history_file()
        self.search_history.load_from_file(history_file)
        self.update_search_suggestions()
    
    def save_search_history(self):
        """Sauvegarde l'historique des recherches"""
        history_file = self.config.get_history_file()
        self.search_history.save_to_file(history_file)

    def closeEvent(self, event):
        """Sauvegarde l'historique lors de la fermeture de l'application"""
        self.save_search_history()
        event.accept()

    def update_search_suggestions(self):
        """Met à jour les suggestions de recherche"""
        recent_searches = self.search_history.get_recent_searches(10)
        self.search_input.clear()
        
        # Créer un modèle de complétion
        completer = QCompleter([search[1] for search in recent_searches], self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.search_input.setCompleter(completer)

    def import_folder(self):
        """Importe un dossier avec une boîte de dialogue améliorée"""
        if not self.db:
            QMessageBox.warning(self, "Erreur", "Aucune base de données n'est ouverte.")
            return
            
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier à importer")
        if not folder:
            return
        
        dialog = ImportFolderDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        
        data = dialog.get_data()
        file_type = data["file_type"]
        tags_to_apply = data["tags"]
        recursive = data["recursive"]
        
        # Compter les fichiers
        import_count = 0
        duplicate_count = 0
        error_count = 0
        tagged_count = 0
        
        progress_dialog = QProgressDialog("Importation des fichiers...", "Annuler", 0, 100, self)
        progress_dialog.setWindowTitle("Importation en cours")
        progress_dialog.setWindowModality(Qt.WindowModal)
        
        # Récupérer la liste de tous les fichiers
        all_files = []
        if recursive:
            # Parcours récursif de tous les sous-dossiers
            for root_dir, dirs, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    all_files.append(file_path)
        else:
            # Seulement les fichiers du dossier racine
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                if os.path.isfile(file_path):
                    all_files.append(file_path)
        
        total_files = len(all_files)
        if total_files == 0:
            QMessageBox.information(self, "Information", "Aucun fichier trouvé dans le dossier sélectionné.")
            return
        
        progress_dialog.setMaximum(total_files)
        
        for i, file_path in enumerate(all_files):
            if progress_dialog.wasCanceled():
                break
            
            # Vérifier si le fichier existe déjà dans la base
            if self.db.location_exists(file_path):
                duplicate_count += 1
                progress_dialog.setValue(i + 1)
                continue
            
            # Déterminer le type de fichier
            actual_type = self.get_file_type_from_extension(file_path)
            if actual_type == "autre":
                actual_type = file_type  # Utiliser le type par défaut si non reconnu
            
            # Créer l'objet
            try:
                # Créer une description avec le chemin relatif
                relative_path = os.path.relpath(file_path, folder)
                obj = FileObject(
                    name=os.path.basename(file_path),  # Nom du fichier comme nom par défaut
                    description=f"Fichier importé depuis: {relative_path}\nDossier: {os.path.basename(folder)}",
                    file_type=actual_type,
                    location=file_path
                )
                
                # Ajouter à la base de données
                obj_id = self.db.add_object(obj)
                if obj_id is not None:
                    import_count += 1
                    
                    # Appliquer les tags si spécifiés
                    if tags_to_apply:
                        for tag in tags_to_apply:
                            self.db.add_tag(obj_id, tag)
                        tagged_count += 1
                else:
                    duplicate_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"Erreur lors de l'import de {file_path}: {e}")
            
            progress_dialog.setValue(i + 1)
            QApplication.processEvents()  # Permet à l'interface de rester responsive
        
        progress_dialog.close()
        
        # Afficher les résultats
        self.load_all_objects()
        
        message = f"Importation terminée !\n\n" \
                f"Fichiers importés: {import_count}\n" \
                f"Fichiers tagués: {tagged_count}\n" \
                f"Fichiers en double ignorés: {duplicate_count}\n" \
                f"Erreurs: {error_count}"
        
        if tags_to_apply:
            tags_str = ", ".join([f"#{tag}" for tag in tags_to_apply])
            message += f"\n\nTags appliqués: {tags_str}"
        
        if duplicate_count > 0:
            message += "\n\nLes fichiers en double ont été automatiquement ignorés."
        
        QMessageBox.information(self, "Importation terminée", message)

        def parse_tags(self, tags_input: str) -> List[str]:
            """Parse une chaîne de tags en liste de tags nettoyés"""
            if not tags_input.strip():
                return []
            
            # Séparer par espaces, virgules, points-virgules, etc.
            raw_tags = re.split(r'[,\s;]+', tags_input.strip())
            
            # Nettoyer et filtrer les tags vides
            cleaned_tags = []
            for tag in raw_tags:
                cleaned_tag = tag.strip().lstrip('#')  # Enlever les # au début
                if cleaned_tag:  # Ignorer les tags vides
                    cleaned_tags.append(cleaned_tag)
            
            return cleaned_tags

    def get_file_type_from_extension(self, file_path):
        """Détermine le type de fichier basé sur l'extension"""
        extension = os.path.splitext(file_path)[1].lower()
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flv']
        audio_extensions = ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']
        document_extensions = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx']
        
        if extension in image_extensions:
            return "image"
        elif extension in video_extensions:
            return "video"
        elif extension in audio_extensions:
            return "audio"
        elif extension in document_extensions:
            return "document"
        else:
            return "autre"

    def init_ui(self):
        self.setWindowTitle("Gestionnaire de Fichiers par Tags")
        self.setGeometry(100, 100, 1400, 800)  # Augmenté la largeur pour accommoder la prévisualisation
        
        # Widget central et layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter pour diviser la fenêtre
        splitter = QSplitter(Qt.Horizontal)
        
        # Panel gauche pour la liste des objets
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Barre de recherche
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par nom ou tag (#tag)...")
        self.search_input.returnPressed.connect(self.perform_search)
        search_button = QPushButton("Rechercher")
        search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        
        # Liste des résultats avec menu contextuel
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.display_object_details)
        self.results_list.itemDoubleClicked.connect(self.open_object_location)
        self.results_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_list.customContextMenuRequested.connect(self.show_context_menu)
        
        left_layout.addLayout(search_layout)
        left_layout.addWidget(QLabel("Résultats:"))
        left_layout.addWidget(self.results_list)
        
        # Panel central pour les détails et gestion des tags
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        # Détails de l'objet
        details_group = QGroupBox("Détails de l'objet")
        details_layout = QVBoxLayout()
        
        self.name_label = QLabel("Nom: ")
        self.type_label = QLabel("Type: ")
        self.location_label = QLabel("Emplacement: ")
        
        # Bouton pour ouvrir l'emplacement
        self.open_location_button = QPushButton("Ouvrir l'emplacement")
        self.open_location_button.clicked.connect(self.open_current_object_location)
        self.open_location_button.setEnabled(False)
        
        # Bouton pour modifier l'objet
        self.edit_button = QPushButton("Modifier cet élément")
        self.edit_button.clicked.connect(self.edit_current_object)
        self.edit_button.setEnabled(False)
        
        self.description_view = QTextEdit()
        self.description_view.setReadOnly(True)
        
        details_layout.addWidget(self.name_label)
        details_layout.addWidget(self.type_label)
        details_layout.addWidget(self.location_label)
        
        button_details_layout = QHBoxLayout()
        button_details_layout.addWidget(self.open_location_button)
        button_details_layout.addWidget(self.edit_button)
        details_layout.addLayout(button_details_layout)
        
        details_layout.addWidget(QLabel("Description:"))
        details_layout.addWidget(self.description_view)
        details_group.setLayout(details_layout)
        
        # Gestion des tags
        tags_group = QGroupBox("Gestion des Tags")
        tags_layout = QVBoxLayout()
        
        tag_input_layout = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Ajouter un tag...")
        self.tag_input.returnPressed.connect(self.add_tag_to_object)
        add_tag_button = QPushButton("Ajouter")
        add_tag_button.clicked.connect(self.add_tag_to_object)
        tag_input_layout.addWidget(self.tag_input)
        tag_input_layout.addWidget(add_tag_button)
        
        self.tags_list = QListWidget()
        
        tags_layout.addLayout(tag_input_layout)
        tags_layout.addWidget(QLabel("Tags associés:"))
        tags_layout.addWidget(self.tags_list)
        tags_group.setLayout(tags_layout)
        
        # Boutons d'action
        button_layout = QHBoxLayout()
        add_file_button = QPushButton("Ajouter un fichier")
        add_file_button.clicked.connect(self.add_new_file)
        remove_tag_button = QPushButton("Retirer le tag sélectionné")
        remove_tag_button.clicked.connect(self.remove_tag_from_object)
        
        button_layout.addWidget(add_file_button)
        button_layout.addWidget(remove_tag_button)
        
        center_layout.addWidget(details_group)
        center_layout.addWidget(tags_group)
        center_layout.addLayout(button_layout)
        
        # Panel droit pour la prévisualisation
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Widget de prévisualisation
        self.preview_widget = PreviewWidget()
        right_layout.addWidget(self.preview_widget)
        
        # Ajouter les panels au splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500, 400])  # Ajuster les tailles des panels
        
        main_layout.addWidget(splitter)
        
        # Menu
        self.create_menu()
    
    def toggle_dark_mode(self):
        """Active/désactive le mode sombre"""
        dark_mode = self.dark_mode_action.isChecked()
        self.config.set_dark_mode(dark_mode)
        self.apply_theme()
    
    def apply_theme(self):
        """Applique le thème sombre ou clair selon la configuration"""
        dark_mode = self.config.get_dark_mode()
        
        app = QApplication.instance()
        palette = QPalette()
        
        if dark_mode:
            # Palette pour le mode sombre
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(35, 35, 35))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.black)
            
            # Styles supplémentaires pour les widgets spécifiques
            self.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 1px solid #666;
                    border-radius: 5px;
                    margin-top: 1ex;
                    padding-top: 10px;
                    background-color: #353535;
                    color: white;
                }
                
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    padding: 0 5px;
                }
                
                QListWidget {
                    background-color: #353535;
                    color: white;
                    border: 1px solid #666;
                    border-radius: 3px;
                }
                
                QLineEdit {
                    background-color: #353535;
                    color: white;
                    border: 1px solid #666;
                    border-radius: 3px;
                    padding: 5px;
                }
                
                QTextEdit {
                    background-color: #353535;
                    color: white;
                    border: 1px solid #666;
                    border-radius: 3px;
                }
                
                QComboBox {
                    background-color: #353535;
                    color: white;
                    border: 1px solid #666;
                    border-radius: 3px;
                    padding: 5px;
                }
                
                QComboBox QAbstractItemView {
                    background-color: #353535;
                    color: white;
                    selection-background-color: #2a82da;
                }
                
                QPushButton {
                    background-color: #555;
                    color: white;
                    border: 1px solid #666;
                    border-radius: 3px;
                    padding: 5px 10px;
                }
                
                QPushButton:hover {
                    background-color: #666;
                }
                
                QPushButton:pressed {
                    background-color: #777;
                }
                
                QPushButton:disabled {
                    background-color: #333;
                    color: #888;
                }
            """)
        else:
            # Palette par défaut (mode clair)
            palette.setColor(QPalette.Window, QColor(240, 240, 240))
            palette.setColor(QPalette.WindowText, Qt.black)
            palette.setColor(QPalette.Base, Qt.white)
            palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.black)
            palette.setColor(QPalette.Text, Qt.black)
            palette.setColor(QPalette.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ButtonText, Qt.black)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(0, 0, 255))
            palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
            palette.setColor(QPalette.HighlightedText, Qt.white)
            
            # Réinitialiser le style
            self.setStyleSheet("")
        
        app.setPalette(palette)

    def init_ui(self):
        self.setWindowTitle("Gestionnaire de Fichiers par Tags")
        self.setGeometry(100, 100, 1400, 800)  # Augmenté la largeur pour accommoder la prévisualisation
        
        # Widget central et layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Splitter pour diviser la fenêtre
        splitter = QSplitter(Qt.Horizontal)
        
        # Panel gauche pour la liste des objets
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Barre de recherche
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher par nom ou tag (#tag)...")
        self.search_input.returnPressed.connect(self.perform_search)
        search_button = QPushButton("Rechercher")
        search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        
        # Liste des résultats avec menu contextuel
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.display_object_details)
        self.results_list.itemDoubleClicked.connect(self.open_object_location)
        self.results_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_list.customContextMenuRequested.connect(self.show_context_menu)
        
        left_layout.addLayout(search_layout)
        left_layout.addWidget(QLabel("Résultats:"))
        left_layout.addWidget(self.results_list)
        
        # Panel central pour les détails et gestion des tags
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        # Détails de l'objet
        details_group = QGroupBox("Détails de l'objet")
        details_layout = QVBoxLayout()
        
        self.name_label = QLabel("Nom: ")
        self.type_label = QLabel("Type: ")
        self.location_label = QLabel("Emplacement: ")
        
        # Bouton pour ouvrir l'emplacement
        self.open_location_button = QPushButton("Ouvrir l'emplacement")
        self.open_location_button.clicked.connect(self.open_current_object_location)
        self.open_location_button.setEnabled(False)
        
        # Bouton pour modifier l'objet
        self.edit_button = QPushButton("Modifier cet élément")
        self.edit_button.clicked.connect(self.edit_current_object)
        self.edit_button.setEnabled(False)
        
        self.description_view = QTextEdit()
        self.description_view.setReadOnly(True)
        
        details_layout.addWidget(self.name_label)
        details_layout.addWidget(self.type_label)
        details_layout.addWidget(self.location_label)
        
        button_details_layout = QHBoxLayout()
        button_details_layout.addWidget(self.open_location_button)
        button_details_layout.addWidget(self.edit_button)
        details_layout.addLayout(button_details_layout)
        
        details_layout.addWidget(QLabel("Description:"))
        details_layout.addWidget(self.description_view)
        details_group.setLayout(details_layout)
        
        # Gestion des tags
        tags_group = QGroupBox("Gestion des Tags")
        tags_layout = QVBoxLayout()
        
        tag_input_layout = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("Ajouter un tag...")
        self.tag_input.returnPressed.connect(self.add_tag_to_object)
        add_tag_button = QPushButton("Ajouter")
        add_tag_button.clicked.connect(self.add_tag_to_object)
        tag_input_layout.addWidget(self.tag_input)
        tag_input_layout.addWidget(add_tag_button)
        
        self.tags_list = QListWidget()
        
        tags_layout.addLayout(tag_input_layout)
        tags_layout.addWidget(QLabel("Tags associés:"))
        tags_layout.addWidget(self.tags_list)
        tags_group.setLayout(tags_layout)
        
        # Boutons d'action
        button_layout = QHBoxLayout()
        add_file_button = QPushButton("Ajouter un fichier")
        add_file_button.clicked.connect(self.add_new_file)
        remove_tag_button = QPushButton("Retirer le tag sélectionné")
        remove_tag_button.clicked.connect(self.remove_tag_from_object)
        
        button_layout.addWidget(add_file_button)
        button_layout.addWidget(remove_tag_button)
        
        center_layout.addWidget(details_group)
        center_layout.addWidget(tags_group)
        center_layout.addLayout(button_layout)
        
        # Panel droit pour la prévisualisation
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Widget de prévisualisation
        self.preview_widget = PreviewWidget()
        right_layout.addWidget(self.preview_widget)
        
        # Ajouter les panels au splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(center_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500, 400])  # Ajuster les tailles des panels
        
        main_layout.addWidget(splitter)
        
        # Menu
        self.create_menu()
    
    def create_menu(self):
        menu_bar = self.menuBar()
        
        # Menu Fichier
        file_menu = menu_bar.addMenu("Fichier")
        
        add_file_action = file_menu.addAction("Ajouter un fichier")
        add_file_action.triggered.connect(self.add_new_file)

        # Ajouter l'action d'import de dossier
        import_folder_action = file_menu.addAction("Importer un dossier...")
        import_folder_action.triggered.connect(self.import_folder)
        
        open_db_action = file_menu.addAction("Ouvrir un autre dossier...")
        open_db_action.triggered.connect(self.open_database)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Quitter")
        exit_action.triggered.connect(self.close)
        
        # Menu Édition
        edit_menu = menu_bar.addMenu("Édition")
        
        edit_action = edit_menu.addAction("Modifier l'élément sélectionné")
        edit_action.triggered.connect(self.edit_current_object)
        
        delete_action = edit_menu.addAction("Supprimer l'élément sélectionné")
        delete_action.triggered.connect(self.delete_current_object)
        
        # Menu Recherche
        search_menu = menu_bar.addMenu("Recherche")
        
        history_action = search_menu.addAction("Historique des recherches")
        history_action.triggered.connect(self.show_search_history)
        
        clear_history_action = search_menu.addAction("Effacer l'historique")
        clear_history_action.triggered.connect(self.clear_search_history)
        
        search_menu.addSeparator()
        syntax_help_action = search_menu.addAction("Aide syntaxe recherche")
        syntax_help_action.triggered.connect(self.show_search_help)
        

        # Menu Tags
        tags_menu = menu_bar.addMenu("Tags")
        
        view_tags_action = tags_menu.addAction("Voir tous les tags")
        view_tags_action.triggered.connect(self.show_tags_list)

        # Menu Affichage
        view_menu = menu_bar.addMenu("Affichage")
        
        self.dark_mode_action = QAction("Mode sombre", self)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.setChecked(self.config.get_dark_mode())
        self.dark_mode_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(self.dark_mode_action)
        
        # Menu Aide
        help_menu = menu_bar.addMenu("Aide")
        
        about_action = help_menu.addAction("À propos")
        about_action.triggered.connect(self.show_about)
    
    def show_search_help(self):
        """Affiche l'aide sur la syntaxe de recherche"""
        dialog = SearchHelpDialog(self)
        dialog.exec_()

    def show_tags_list(self):
        """Affiche une boîte de dialogue avec la liste de tous les tags et leur nombre d'objets"""
        if not self.db:
            QMessageBox.warning(self, "Erreur", "Aucune base de données n'est ouverte.")
            return
        
        # Créer une boîte de dialogue
        dialog = QDialog(self)
        dialog.setWindowTitle("Liste des Tags")
        dialog.setModal(True)
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        # Label d'information
        info_label = QLabel(f"Tags disponibles ({len(self.db.tags)}):")
        layout.addWidget(info_label)
        
        # Liste des tags
        tags_list = QListWidget()
        
        # Trier les tags par ordre alphabétique
        sorted_tags = sorted(self.db.tags.items(), key=lambda x: x[0].lower())
        
        for tag, obj_ids in sorted_tags:
            count = len(obj_ids)
            item = QListWidgetItem(f"#{tag} ({count} objet{'s' if count != 1 else ''})")
            item.setData(Qt.UserRole, tag)  # Stocker le tag pour référence
            tags_list.addItem(item)
        
        layout.addWidget(tags_list)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        search_button = QPushButton("Rechercher ce tag")
        search_button.clicked.connect(lambda: self.search_by_tag_from_list(tags_list.currentItem(), dialog))
        
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(dialog.accept)
        
        button_layout.addWidget(search_button)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        # Connecter le double-clic pour rechercher par tag
        tags_list.itemDoubleClicked.connect(lambda item: self.search_by_tag_from_list(item, dialog))
        
        dialog.exec_()
    
    def search_by_tag_from_list(self, item, dialog=None):
        """Effectue une recherche basée sur le tag sélectionné dans la liste"""
        if not item:
            return
        
        tag = item.data(Qt.UserRole)
        if tag:
            self.search_input.setText(f"#{tag}")
            self.perform_search()
            # Fermer la boîte de dialogue si elle est fournie
            if dialog:
                dialog.accept()

    def show_context_menu(self, position):
        """Affiche le menu contextuel pour la liste des résultats"""
        if not self.db:
            return
            
        item = self.results_list.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        
        edit_action = menu.addAction("Modifier")
        edit_action.triggered.connect(lambda: self.edit_object(item))
        
        delete_action = menu.addAction("Supprimer")
        delete_action.triggered.connect(lambda: self.delete_object(item))
        
        menu.exec_(self.results_list.mapToGlobal(position))
    
    def load_database(self):
        """Charge la base de données"""
        # Vérifier si c'est le premier démarrage
        if self.config.is_first_run():
            self.show_first_run_dialog()
        else:
            data_dir = self.config.get_data_dir()
            self.setup_database(data_dir)
    
    def show_first_run_dialog(self):
        """Affiche la boîte de dialogue de premier démarrage"""
        dialog = FirstRunDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data_dir = dialog.get_data_dir()
            self.config.set_data_dir(data_dir)
            self.config.set_first_run_complete()
            self.setup_database(data_dir)
        else:
            # Si l'utilisateur annule, on quitte l'application
            QApplication.quit()
    
    def setup_database(self, data_dir):
        """Configure la base de données avec le dossier spécifié"""
        try:
            self.db = TagDatabase(data_dir)
            self.load_all_objects()
            self.setWindowTitle(f"Gestionnaire de Fichiers par Tags - {data_dir}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger la base de données: {e}")
    
    def open_database(self):
        """Ouvre un autre dossier de base de données"""
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier de données")
        if folder:
            self.config.set_data_dir(folder)
            self.setup_database(folder)
    
    def load_all_objects(self):
        """Charge tous les objets dans la liste"""
        if not self.db:
            return
            
        self.results_list.clear()
        for obj in self.db.objects.values():
            item = QListWidgetItem(f"{obj.name} ({obj.file_type})")
            item.setData(Qt.UserRole, obj.id)
            self.results_list.addItem(item)
        
        # Effacer la prévisualisation et désactiver les boutons
        self.preview_widget.clear_preview()
        self.open_location_button.setEnabled(False)
        self.edit_button.setEnabled(False)
        self.current_object = None
    
    def perform_search(self):
        """Effectue une recherche en fonction du texte saisi"""
        if not self.db:
            QMessageBox.warning(self, "Erreur", "Aucune base de données n'est ouverte.")
            return
            
        query = self.search_input.text().strip()
        if not query:
            self.load_all_objects()
            return
        
        # Sauvegarder le texte de recherche avant d'ajouter à l'historique
        search_text = query
        
        # Ajouter à l'historique
        self.search_history.add_search(query)
        self.update_search_suggestions()
        self.save_search_history()
        
        # Utiliser la recherche avancée pour toutes les requêtes
        results = self.db.advanced_search(query)
        
        # Afficher les résultats
        self.display_search_results(results, query)
        
        # REMETTRE le texte de recherche dans la barre après la recherche
        self.search_input.setText(search_text)
        # Positionner le curseur à la fin du texte
        self.search_input.setCursorPosition(len(search_text))

    def display_search_results(self, results: List[FileObject], query: str = ""):
        """Affiche les résultats de recherche"""
        self.results_list.clear()
        
        for obj in results:
            item = QListWidgetItem(f"{obj.name} ({obj.file_type})")
            item.setData(Qt.UserRole, obj.id)
            self.results_list.addItem(item)
        
        # Afficher le nombre de résultats et la requête
        if results:
            count_text = f"--- {len(results)} résultat(s)"
            if query:
                count_text += f" pour: {query}"
            count_text += " ---"
            
            count_item = QListWidgetItem(count_text)
            count_item.setFlags(Qt.NoItemFlags)
            count_item.setForeground(Qt.darkGray)
            self.results_list.addItem(count_item)
        
        # Effacer la prévisualisation si aucun résultat
        if not results:
            self.preview_widget.clear_preview()
            self.open_location_button.setEnabled(False)
            self.edit_button.setEnabled(False)
            
            if query:
                QMessageBox.information(self, "Recherche", 
                                      f"Aucun résultat trouvé pour: {query}")

    

    def show_search_history(self):
        """Affiche la boîte de dialogue d'historique des recherches"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Historique des recherches")
        dialog.setModal(True)
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Liste de l'historique
        history_list = QListWidget()
        
        for timestamp, query in self.search_history.history:
            item = QListWidgetItem(f"{timestamp} - {query}")
            item.setData(Qt.UserRole, query)
            history_list.addItem(item)
        
        layout.addWidget(QLabel("Historique des recherches récentes:"))
        layout.addWidget(history_list)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        search_button = QPushButton("Rechercher à nouveau")
        search_button.clicked.connect(lambda: self.reuse_search_query(history_list.currentItem(), dialog))
        
        clear_button = QPushButton("Effacer l'historique")
        clear_button.clicked.connect(lambda: self.clear_search_history(dialog))
        
        close_button = QPushButton("Fermer")
        close_button.clicked.connect(dialog.accept)
        
        button_layout.addWidget(search_button)
        button_layout.addWidget(clear_button)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        # Connecter le double-clic pour réutiliser la recherche
        history_list.itemDoubleClicked.connect(lambda item: self.reuse_search_query(item, dialog))
        
        dialog.exec_()

    def reuse_search_query(self, item, dialog=None):
        """Réutilise une recherche de l'historique"""
        if not item:
            return
        
        query = item.data(Qt.UserRole)
        if query:
            self.search_input.setText(query)
            self.perform_search()
            if dialog:
                dialog.accept()
    
    def clear_search_history(self, dialog=None):
        """Efface tout l'historique des recherches"""
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Êtes-vous sûr de vouloir effacer tout l'historique des recherches ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.search_history.clear_history()
            self.update_search_suggestions()
            self.save_search_history()
            
            if dialog:
                dialog.accept()
            
            QMessageBox.information(self, "Succès", "Historique des recherches effacé.")

    def display_object_details(self, item):
        """Affiche les détails de l'objet sélectionné"""
        if not self.db:
            return
            
        obj_id = item.data(Qt.UserRole)
        self.current_object = self.db.objects.get(obj_id)
        
        if self.current_object:
            self.name_label.setText(f"Nom: {self.current_object.name}")
            self.type_label.setText(f"Type: {self.current_object.file_type}")
            
            # Afficher l'emplacement avec un style différent selon le type
            location_text = f"Emplacement: {self.current_object.location}"
            if self.current_object.is_external():
                location_text += " 🌐"  # Icône pour les URLs web
            else:
                location_text += " 💾"  # Icône pour les fichiers locaux
            
            self.location_label.setText(location_text)
            self.description_view.setText(self.current_object.description)
            
            # Activer les boutons
            self.open_location_button.setEnabled(True)
            self.edit_button.setEnabled(True)
            
            # Charger les tags associés
            self.tags_list.clear()
            tags = self.db.get_object_tags(obj_id)
            for tag in tags:
                self.tags_list.addItem(f"#{tag}")
            
            # Afficher la prévisualisation
            self.preview_widget.set_preview(self.current_object)
        else:
            # Effacer la prévisualisation si l'objet n'est pas trouvé
            self.preview_widget.clear_preview()
            self.open_location_button.setEnabled(False)
            self.edit_button.setEnabled(False)

    def open_current_object_location(self):
        """Ouvre l'emplacement de l'objet courant"""
        if self.current_object:
            success = self.current_object.open_location()
            if not success:
                QMessageBox.warning(self, "Erreur", "Impossible d'ouvrir l'emplacement. Le fichier n'existe pas ou l'URL est invalide.")
    
    def open_object_location(self, item):
        """Ouvre l'emplacement de l'objet double-cliqué"""
        if not self.db:
            return
            
        obj_id = item.data(Qt.UserRole)
        obj = self.db.objects.get(obj_id)
        if obj:
            success = obj.open_location()
            if not success:
                QMessageBox.warning(self, "Erreur", "Impossible d'ouvrir l'emplacement. Le fichier n'existe pas ou l'URL est invalide.")
    
    def add_tag_to_object(self):
        """Ajoute un tag à l'objet courant"""
        if not self.db:
            QMessageBox.warning(self, "Erreur", "Aucune base de données n'est ouverte.")
            return
            
        if not self.current_object:
            QMessageBox.warning(self, "Erreur", "Aucun objet sélectionné.")
            return
        
        tag = self.tag_input.text().strip()
        if not tag:
            return
        
        self.db.add_tag(self.current_object.id, tag)
        self.display_object_details(self.results_list.currentItem())
        self.tag_input.clear()
    
    def remove_tag_from_object(self):
        """Retire le tag sélectionné de l'objet courant"""
        if not self.db:
            QMessageBox.warning(self, "Erreur", "Aucune base de données n'est ouverte.")
            return
            
        if not self.current_object:
            QMessageBox.warning(self, "Erreur", "Aucun objet sélectionné.")
            return
        
        current_tag_item = self.tags_list.currentItem()
        if not current_tag_item:
            return
        
        tag = current_tag_item.text().lstrip('#')
        self.db.remove_tag(self.current_object.id, tag)
        self.display_object_details(self.results_list.currentItem())
    
    def add_new_file(self):
        """Ouvre une boîte de dialogue pour ajouter un nouveau fichier"""
        if not self.db:
            QMessageBox.warning(self, "Erreur", "Aucune base de données n'est ouverte.")
            return
            
        dialog = FileDialog(self)
        
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            
            # Validation de l'emplacement
            location = data["location"].strip()
            location_type = dialog.location_type_combo.currentText()
            
            if location_type == "Interne (fichier local)" and not os.path.exists(location):
                QMessageBox.warning(self, "Erreur", "Le fichier spécifié n'existe pas.")
                return
            
            if location_type == "Externe (URL web)" and not location.startswith(('http://', 'https://')):
                QMessageBox.warning(self, "Erreur", "L'URL doit commencer par http:// ou https://")
                return
            
            # Vérifier si l'emplacement existe déjà
            if self.db.location_exists(location):
                existing_obj = self.db.get_object_by_location(location)
                QMessageBox.warning(
                    self, 
                    "Fichier déjà existant", 
                    f"Cet emplacement existe déjà dans la base de données:\n\n"
                    f"Nom: {existing_obj.name}\n"
                    f"Type: {existing_obj.file_type}\n\n"
                    f"Vous ne pouvez pas ajouter le même fichier deux fois."
                )
                return
            
            # Créer le nouvel objet
            new_obj = FileObject(
                data["name"],
                data["description"],
                data["type"],
                location
            )
            
            # Ajouter à la base de données
            obj_id = self.db.add_object(new_obj)
            
            if obj_id is None:
                QMessageBox.warning(self, "Erreur", "Impossible d'ajouter le fichier (doublon).")
                return
            
            # Mettre à jour l'interface
            self.load_all_objects()
            
            QMessageBox.information(self, "Succès", "Fichier ajouté avec succès.")
    
    def edit_current_object(self):
        """Modifie l'objet courant"""
        if not self.current_object:
            QMessageBox.warning(self, "Erreur", "Aucun objet sélectionné.")
            return
            
        self.edit_object_by_id(self.current_object.id)
    
    def edit_object(self, item):
        """Modifie l'objet sélectionné dans la liste"""
        if not item:
            return
            
        obj_id = item.data(Qt.UserRole)
        self.edit_object_by_id(obj_id)
    
    def edit_object_by_id(self, obj_id):
        """Modifie un objet par son ID en vérifiant les doublons"""
        if not self.db:
            QMessageBox.warning(self, "Erreur", "Aucune base de données n'est ouverte.")
            return
            
        obj = self.db.objects.get(obj_id)
        if not obj:
            QMessageBox.warning(self, "Erreur", "Objet introuvable.")
            return
        
        dialog = FileDialog(self, obj)
        
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            
            # Validation de l'emplacement
            location = data["location"].strip()
            location_type = dialog.location_type_combo.currentText()
            
            if location_type == "Interne (fichier local)" and not os.path.exists(location):
                QMessageBox.warning(self, "Erreur", "Le fichier spécifié n'existe pas.")
                return
            
            if location_type == "Externe (URL web)" and not location.startswith(('http://', 'https://')):
                QMessageBox.warning(self, "Erreur", "L'URL doit commencer par http:// ou https://")
                return
            
            # Vérifier si le nouvel emplacement existe déjà pour un autre objet
            if location != obj.location:  # Seulement si l'emplacement change
                if self.db.location_exists(location):
                    existing_obj = self.db.get_object_by_location(location)
                    QMessageBox.warning(
                        self, 
                        "Emplacement déjà existant", 
                        f"Cet emplacement existe déjà pour un autre objet:\n\n"
                        f"Nom: {existing_obj.name}\n"
                        f"Type: {existing_obj.file_type}\n\n"
                        f"Vous ne pouvez pas utiliser le même emplacement pour deux objets différents."
                    )
                    return
            
            # Mettre à jour l'objet
            success = self.db.update_object(
                obj_id,
                data["name"],
                data["description"],
                data["type"],
                location
            )
            
            if success:
                # Mettre à jour l'interface
                self.load_all_objects()
                QMessageBox.information(self, "Succès", "Fichier modifié avec succès.")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de modifier le fichier (doublon détecté).")
    
    def delete_current_object(self):
        """Supprime l'objet courant"""
        if not self.current_object:
            QMessageBox.warning(self, "Erreur", "Aucun objet sélectionné.")
            return
            
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Êtes-vous sûr de vouloir supprimer '{self.current_object.name}' ?\nCette action est irréversible.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.db.delete_object(self.current_object.id)
            if success:
                self.load_all_objects()
                QMessageBox.information(self, "Succès", "Fichier supprimé avec succès.")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de supprimer le fichier.")
    
    def delete_object(self, item):
        """Supprime l'objet sélectionné dans la liste"""
        if not item:
            return
            
        obj_id = item.data(Qt.UserRole)
        obj = self.db.objects.get(obj_id)
        
        if not obj:
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
                self.load_all_objects()
                QMessageBox.information(self, "Succès", "Fichier supprimé avec succès.")
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de supprimer le fichier.")
    
    def show_about(self):
        """Affiche la boîte de dialogue À propos"""
        data_dir = self.config.get_data_dir() if self.db else "Non spécifié"
        QMessageBox.about(self, "À propos", 
                         f"Gestionnaire de Fichiers par Tags\n\n"
                         f"Cette application permet de gérer vos fichiers à l'aide de tags.\n"
                         f"Vous pouvez rechercher des fichiers par nom ou par tags en utilisant "
                         f"une syntaxe avancée (AND, OR, NOT).\n\n"
                         f"Dossier de données actuel: {data_dir}\n\n"
                         f"Les emplacements peuvent être:\n"
                         f"- Internes: chemins vers des fichiers locaux\n"
                         f"- Externes: URLs web (http://, https://)\n\n"
                         f"Nouveau: Prévisualisation des images et modification des éléments!")

def test_boolean_search():
    """Tests pour la recherche booléenne"""
    # Créer une base de test
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    db = TagDatabase(temp_dir)
    
    try:
        # Créer des objets de test
        obj1 = FileObject("chat.jpg", "Photo de chat", "image", "/tmp/chat.jpg")
        obj2 = FileObject("chien.jpg", "Photo de chien", "image", "/tmp/chien.jpg")
        obj3 = FileObject("chat et chien.jpg", "Photo groupe", "image", "/tmp/chat_chien.jpg")
        
        db.add_object(obj1)
        db.add_object(obj2)
        db.add_object(obj3)
        
        # Ajouter des tags
        db.add_tag(obj1.id, "animal")
        db.add_tag(obj2.id, "animal")
        db.add_tag(obj3.id, "groupe")
        db.add_tag(obj3.id, "animal")
        
        print("Testing boolean search...")
        
        # Tests de recherche
        result = db.advanced_search("chat")
        print(f"chat: {len(result)} résultats")
        assert len(result) == 2, f"Expected 2, got {len(result)}"
        
        result = db.advanced_search("chien")
        print(f"chien: {len(result)} résultats")
        assert len(result) == 2, f"Expected 2, got {len(result)}"
        
        result = db.advanced_search("chat AND chien")
        print(f"chat AND chien: {len(result)} résultats")
        assert len(result) == 1, f"Expected 1, got {len(result)}"
        
        result = db.advanced_search("chat OR chien")
        print(f"chat OR chien: {len(result)} résultats")
        assert len(result) == 3, f"Expected 3, got {len(result)}"
        
        # Test NOT avec espaces
        result = db.advanced_search("chat NOT chien")
        print(f"chat NOT chien: {len(result)} résultats")
        assert len(result) == 1, f"Expected 1, got {len(result)}"
        
        # Test avec tags
        result = db.advanced_search("#animal")
        print(f"#animal: {len(result)} résultats")
        assert len(result) == 3, f"Expected 3, got {len(result)}"
        
        result = db.advanced_search("#animal AND #groupe")
        print(f"#animal AND #groupe: {len(result)} résultats")
        assert len(result) == 1, f"Expected 1, got {len(result)}"
        
        result = db.advanced_search("(chat OR chien) AND #groupe")
        print(f"(chat OR chien) AND #groupe: {len(result)} résultats")
        assert len(result) == 1, f"Expected 1, got {len(result)}"
        
        print("✓ Tous les tests de recherche booléenne ont réussi")
        
    except Exception as e:
        print(f"✗ Erreur dans les tests: {e}")
        import traceback
        traceback.print_exc()
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    # Lancer les tests au démarrage
    test_boolean_search()
    
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())