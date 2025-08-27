import os
import json
import uuid
import re
import datetime
from collections import deque
from typing import List, Dict, Set, Optional
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel, 
                             QTextEdit, QComboBox, QFileDialog, QMessageBox, QSplitter,
                             QTreeWidget, QTreeWidgetItem, QTabWidget, QGroupBox, QDialog,
                             QMenu, QAction, QCompleter, QInputDialog, QProgressDialog)
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
        self.objects: Dict[str, FileObject] = {}  # ID -> FileObject
        self.tags: Dict[str, Set[str]] = {}       # Tag -> Set d'IDs
        self.tag_files: Dict[str, str] = {}       # Tag -> Chemin du fichier
        
        # Créer le répertoire de données s'il n'existe pas
        os.makedirs(data_dir, exist_ok=True)
        self.load_data()
    
    def load_data(self):
        """Charge les données depuis les fichiers JSON"""
        # Charger les objets
        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json") and not filename.startswith("tag_"):
                try:
                    with open(os.path.join(self.data_dir, filename), 'r', encoding='utf-8') as f:
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
        for filename in os.listdir(self.data_dir):
            if filename.startswith("tag_") and filename.endswith(".json"):
                try:
                    tag_name = filename[4:-5]  # Enlever "tag_" et ".json"
                    with open(os.path.join(self.data_dir, filename), 'r', encoding='utf-8') as f:
                        obj_ids = json.load(f)
                        self.tags[tag_name] = set(obj_ids)
                        self.tag_files[tag_name] = os.path.join(self.data_dir, filename)
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
        obj_file = os.path.join(self.data_dir, f"{obj_id}.json")
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
        obj_path = os.path.join(self.data_dir, f"{obj.id}.json")
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
            tag_file_path = os.path.join(self.data_dir, f"tag_{clean_tag}.json")
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
        """Recherche des objets par tag"""
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
        """Recherche avancée avec syntaxe complexe"""
        # Pour les requêtes simples sans opérateurs, utiliser search_by_name
        if not any(op in query for op in [' OR ', ' AND ', ' NOT ', '(', ')']):
            return self.search_by_name(query)
        
        # Cette implémentation est simplifiée pour le prototype
        # Une version complète nécessiterait un parser plus sophistiqué
        
        # Séparer les termes de recherche
        terms = re.split(r'\s+(?:OR|AND|,)\s+', query)
        
        results = []
        for term in terms:
            # Gérer la négation (NOT)
            if term.startswith('not(') and term.endswith(')'):
                negated_term = term[4:-1].strip()
                # Implémenter la logique d'exclusion
                continue
            
            # Gérer les tags (commençant par #)
            if term.startswith('#'):
                results.extend(self.search_by_tag(term))
            else:
                results.extend(self.search_by_name(term))
        
        return list(set(results))  # Éliminer les doublons

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
        """Importe tous les fichiers d'un dossier en évitant les doublons"""
        if not self.db:
            QMessageBox.warning(self, "Erreur", "Aucune base de données n'est ouverte.")
            return
            
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier à importer")
        if not folder:
            return
        
        # Demander le type de fichier par défaut
        file_type, ok = QInputDialog.getItem(
            self,
            "Type de fichier",
            "Sélectionnez le type de fichier par défaut:",
            ["image", "video", "audio", "document", "autre"],
            0,  # Index par défaut
            False  # Non éditable
        )
        
        if not ok:
            return
        
        # Compter les fichiers
        import_count = 0
        duplicate_count = 0
        error_count = 0
        
        progress_dialog = QProgressDialog("Importation des fichiers...", "Annuler", 0, 100, self)
        progress_dialog.setWindowTitle("Importation en cours")
        progress_dialog.setWindowModality(Qt.WindowModal)
        
        # Récupérer la liste de tous les fichiers d'abord pour connaître le total
        all_files = []
        for root_dir, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root_dir, file)
                all_files.append(file_path)
        
        total_files = len(all_files)
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
                obj = FileObject(
                    name=os.path.basename(file_path),  # Nom du fichier comme nom par défaut
                    description=f"Fichier importé automatiquement depuis: {file_path}",
                    file_type=actual_type,
                    location=file_path
                )
                
                # Ajouter à la base de données
                obj_id = self.db.add_object(obj)
                if obj_id is not None:
                    import_count += 1
                else:
                    duplicate_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"Erreur lors de l'import de {file_path}: {e}")
            
            progress_dialog.setValue(i + 1)
        
        progress_dialog.close()
        
        # Afficher les résultats
        self.load_all_objects()
        
        message = f"Importation terminée !\n\n" \
                f"Fichiers importés: {import_count}\n" \
                f"Fichiers en double ignorés: {duplicate_count}\n" \
                f"Erreurs: {error_count}"
        
        if duplicate_count > 0:
            message += "\n\nLes fichiers en double ont été automatiquement ignorés."
        
        QMessageBox.information(self, "Importation terminée", message)

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
        
         
        # Ajouter à l'historique
        self.search_history.add_search(query)
        self.update_search_suggestions()
        self.save_search_history()  # Sauvegarder après chaque recherche

        results = []
        
        # Vérifier si la requête contient des tags (#)
        if '#' in query:
            # Séparer les termes de recherche
            search_terms = query.split()
            tag_terms = []
            name_terms = []
            
            # Séparer les tags et les termes de nom
            for term in search_terms:
                if term.startswith('#'):
                    tag_terms.append(term)
                else:
                    name_terms.append(term)
            
            # Recherche par tags
            tag_results = []
            if tag_terms:
                for tag_term in tag_terms:
                    tag_results.extend(self.db.search_by_tag(tag_term))
                
                # Si plusieurs tags, intersection (ET logique)
                if len(tag_terms) > 1:
                    temp_results = []
                    for obj in tag_results:
                        if tag_results.count(obj) == len(tag_terms):
                            temp_results.append(obj)
                    tag_results = list(set(temp_results))
            
            # Recherche par nom
            name_results = []
            if name_terms:
                name_query = ' '.join(name_terms)
                name_results = self.db.search_by_name(name_query)
            
            # Combiner les résultats
            if tag_results and name_results:
                # Intersection des résultats tags et noms
                results = [obj for obj in tag_results if obj in name_results]
            elif tag_results:
                results = tag_results
            elif name_results:
                results = name_results
        
        else:
            # Recherche avancée pour les requêtes complexes
            if any(op in query for op in [' OR ', ' AND ', ' NOT ', '(', ')']):
                results = self.db.advanced_search(query)
            else:
                # Recherche par nom avec plusieurs mots (ET logique)
                results = self.db.search_by_name(query)
        
        # Afficher les résultats
        self.results_list.clear()
        for obj in results:
            item = QListWidgetItem(f"{obj.name} ({obj.file_type})")
            item.setData(Qt.UserRole, obj.id)
            self.results_list.addItem(item)
        
        # Afficher le nombre de résultats
        if results:
            count_item = QListWidgetItem(f"--- {len(results)} résultat(s) trouvé(s) ---")
            count_item.setFlags(Qt.NoItemFlags)  # Rendre l'item non sélectionnable
            self.results_list.addItem(count_item)
        
        # Effacer la prévisualisation si aucun résultat
        if not results:
            self.preview_widget.clear_preview()
            self.open_location_button.setEnabled(False)
            self.edit_button.setEnabled(False)

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

# Point d'entrée de l'application
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())