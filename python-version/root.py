import os
import json
import uuid
import re
from typing import List, Dict, Set, Optional
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel, 
                             QTextEdit, QComboBox, QFileDialog, QMessageBox, QSplitter,
                             QTreeWidget, QTreeWidgetItem, QTabWidget, QGroupBox, QDialog,
                             QMenu, QAction, QStyleFactory, QActionGroup)
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
    
    def get_theme(self):
        """Retourne le thème actuel"""
        return self.settings.value("theme", "light", type=str)
    
    def set_theme(self, theme):
        """Définit le thème"""
        self.settings.setValue("theme", theme)

class ThemeManager:
    """Gestionnaire de thèmes pour l'application"""
    @staticmethod
    def apply_theme(app, theme_name):
        """Applique un thème à l'application"""
        if theme_name == "dark":
            ThemeManager.apply_dark_theme(app)
        else:
            ThemeManager.apply_light_theme(app)
    
    @staticmethod
    def apply_dark_theme(app):
        """Applique le thème sombre"""
        # Palette de couleurs sombre
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(160, 160, 160))
        dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(160, 160, 160))
        
        app.setPalette(dark_palette)
        
        # Style CSS supplémentaire pour le mode sombre
        dark_stylesheet = """
        QMainWindow, QDialog, QWidget {
            background-color: #353535;
            color: #ffffff;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #555555;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
            background-color: #404040;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #cccccc;
        }
        QLineEdit, QTextEdit, QComboBox {
            background-color: #252525;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px;
        }
        QListWidget, QTreeWidget {
            background-color: #252525;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 3px;
            alternate-background-color: #303030;
        }
        QListWidget::item:selected, QTreeWidget::item:selected {
            background-color: #2a82da;
            color: #ffffff;
        }
        QListWidget::item:hover, QTreeWidget::item:hover {
            background-color: #3a3a3a;
        }
        QPushButton {
            background-color: #505050;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 3px;
            padding: 5px 10px;
        }
        QPushButton:hover {
            background-color: #606060;
        }
        QPushButton:pressed {
            background-color: #404040;
        }
        QPushButton:disabled {
            background-color: #353535;
            color: #888888;
        }
        QMenuBar {
            background-color: #404040;
            color: #ffffff;
        }
        QMenuBar::item {
            background-color: transparent;
            color: #ffffff;
        }
        QMenuBar::item:selected {
            background-color: #505050;
        }
        QMenu {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
        }
        QMenu::item:selected {
            background-color: #2a82da;
        }
        QLabel {
            color: #ffffff;
        }
        QSplitter::handle {
            background-color: #505050;
        }
        QScrollBar:vertical {
            border: 1px solid #555555;
            background: #353535;
            width: 15px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:vertical {
            background: #505050;
            min-height: 20px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            background: none;
        }
        """
        app.setStyleSheet(dark_stylesheet)
    
    @staticmethod
    def apply_light_theme(app):
        """Applique le thème clair (par défaut)"""
        # Réinitialiser la palette
        app.setPalette(app.style().standardPalette())
        # Réinitialiser la feuille de style
        app.setStyleSheet("")

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
    
    def add_object(self, obj: FileObject) -> None:
        """Ajoute un objet à la base de données"""
        self.objects[obj.id] = obj
        self.save_object(obj)
        return obj.id
    
    def update_object(self, obj_id: str, name: str, description: str, file_type: str, location: str) -> bool:
        """Met à jour un objet existant"""
        if obj_id not in self.objects:
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
        self.init_ui()
        self.load_database()
        self.apply_theme()
    
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
        
        # Menu Affichage
        view_menu = menu_bar.addMenu("Affichage")
        
        self.light_theme_action = QAction("Thème clair", self)
        self.light_theme_action.setCheckable(True)
        self.light_theme_action.triggered.connect(lambda: self.toggle_theme("light"))
        
        self.dark_theme_action = QAction("Thème sombre", self)
        self.dark_theme_action.setCheckable(True)
        self.dark_theme_action.triggered.connect(lambda: self.toggle_theme("dark"))
        
        # Grouper les actions de thème
        theme_group = QActionGroup(self)
        theme_group.addAction(self.light_theme_action)
        theme_group.addAction(self.dark_theme_action)
        
        view_menu.addAction(self.light_theme_action)
        view_menu.addAction(self.dark_theme_action)
        
        # Menu Aide
        help_menu = menu_bar.addMenu("Aide")
        
        about_action = help_menu.addAction("À propos")
        about_action.triggered.connect(self.show_about)
    
    def apply_theme(self):
        """Applique le thème sauvegardé"""
        theme = self.config.get_theme()
        ThemeManager.apply_theme(QApplication.instance(), theme)
        
        # Mettre à jour les sélections du menu
        if theme == "light":
            self.light_theme_action.setChecked(True)
        else:
            self.dark_theme_action.setChecked(True)
    
    def toggle_theme(self, theme_name):
        """Bascule entre les thèmes"""
        self.config.set_theme(theme_name)
        self.apply_theme()
    
    def load_database(self):
        """Charge la base de données"""
        data_dir = self.config.get_data_dir()
        try:
            self.db = TagDatabase(data_dir)
            self.update_results_list()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger la base de données: {e}")
    
    def open_database(self):
        """Ouvre une boîte de dialogue pour choisir un autre dossier de données"""
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier de données")
        if folder:
            self.config.set_data_dir(folder)
            self.load_database()
    
    def add_new_file(self):
        """Ouvre la boîte de dialogue pour ajouter un nouveau fichier"""
        dialog = FileDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["name"] or not data["location"]:
                QMessageBox.warning(self, "Champs manquants", "Le nom et l'emplacement sont obligatoires.")
                return
            
            obj = FileObject(data["name"], data["description"], data["type"], data["location"])
            obj_id = self.db.add_object(obj)
            
            # Ajouter des tags si spécifiés dans le nom ou la description
            content = f"{data['name']} {data['description']}"
            tags = re.findall(r'#(\w+)', content)
            for tag in tags:
                self.db.add_tag(obj_id, tag)
            
            self.update_results_list()
            QMessageBox.information(self, "Succès", f"Fichier '{data['name']}' ajouté avec succès.")
    
    def edit_current_object(self):
        """Ouvre la boîte de dialogue pour modifier l'objet actuel"""
        if not self.current_object:
            return
        
        dialog = FileDialog(self, self.current_object)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if not data["name"] or not data["location"]:
                QMessageBox.warning(self, "Champs manquants", "Le nom et l'emplacement sont obligatoires.")
                return
            
            success = self.db.update_object(
                self.current_object.id,
                data["name"],
                data["description"],
                data["type"],
                data["location"]
            )
            
            if success:
                # Mettre à jour l'objet courant
                self.current_object.name = data["name"]
                self.current_object.description = data["description"]
                self.current_object.file_type = data["type"]
                self.current_object.location = data["location"]
                
                self.display_object_details()
                self.update_results_list()
                QMessageBox.information(self, "Succès", "Fichier modifié avec succès.")
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de modifier le fichier.")
    
    def delete_current_object(self):
        """Supprime l'objet actuellement sélectionné"""
        if not self.current_object:
            return
        
        reply = QMessageBox.question(
            self, 
            "Confirmer la suppression", 
            f"Êtes-vous sûr de vouloir supprimer '{self.current_object.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success = self.db.delete_object(self.current_object.id)
            if success:
                self.current_object = None
                self.clear_object_details()
                self.update_results_list()
                QMessageBox.information(self, "Succès", "Fichier supprimé avec succès.")
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de supprimer le fichier.")
    
    def perform_search(self):
        """Effectue une recherche selon les termes saisis"""
        query = self.search_input.text().strip()
        if not query:
            self.update_results_list()
            return
        
        # Recherche par tag si le terme commence par #
        if query.startswith('#'):
            results = self.db.search_by_tag(query)
        else:
            # Recherche avancée si la requête contient des opérateurs
            if any(op in query for op in [' OR ', ' AND ', ' NOT ', '(', ')']):
                results = self.db.advanced_search(query)
            else:
                # Recherche simple par nom
                results = self.db.search_by_name(query)
        
        self.display_results(results)
    
    def update_results_list(self):
        """Met à jour la liste des résultats avec tous les objets"""
        if self.db:
            self.display_results(list(self.db.objects.values()))
    
    def display_results(self, results):
        """Affiche les résultats dans la liste"""
        self.results_list.clear()
        for obj in results:
            item = QListWidgetItem(obj.name)
            item.setData(Qt.UserRole, obj.id)
            self.results_list.addItem(item)
    
    def display_object_details(self):
        """Affiche les détails de l'objet sélectionné"""
        current_item = self.results_list.currentItem()
        if not current_item:
            return
        
        obj_id = current_item.data(Qt.UserRole)
        if obj_id in self.db.objects:
            self.current_object = self.db.objects[obj_id]
            
            # Mettre à jour les labels
            self.name_label.setText(f"Nom: {self.current_object.name}")
            self.type_label.setText(f"Type: {self.current_object.file_type}")
            self.location_label.setText(f"Emplacement: {self.current_object.location}")
            self.description_view.setPlainText(self.current_object.description)
            
            # Activer les boutons
            self.open_location_button.setEnabled(True)
            self.edit_button.setEnabled(True)
            
            # Mettre à jour les tags
            self.update_tags_list()
            
            # Mettre à jour la prévisualisation
            self.preview_widget.set_preview(self.current_object)
    
    def clear_object_details(self):
        """Efface les détails de l'objet"""
        self.name_label.setText("Nom: ")
        self.type_label.setText("Type: ")
        self.location_label.setText("Emplacement: ")
        self.description_view.clear()
        self.tags_list.clear()
        self.open_location_button.setEnabled(False)
        self.edit_button.setEnabled(False)
        self.preview_widget.clear_preview()
    
    def update_tags_list(self):
        """Met à jour la liste des tags pour l'objet courant"""
        self.tags_list.clear()
        if self.current_object:
            tags = self.db.get_object_tags(self.current_object.id)
            for tag in tags:
                self.tags_list.addItem(f"#{tag}")
    
    def add_tag_to_object(self):
        """Ajoute un tag à l'objet courant"""
        if not self.current_object:
            return
        
        tag = self.tag_input.text().strip()
        if not tag:
            return
        
        self.db.add_tag(self.current_object.id, tag)
        self.update_tags_list()
        self.tag_input.clear()
    
    def remove_tag_from_object(self):
        """Retire le tag sélectionné de l'objet courant"""
        if not self.current_object:
            return
        
        current_tag_item = self.tags_list.currentItem()
        if not current_tag_item:
            return
        
        tag = current_tag_item.text().lstrip('#')
        self.db.remove_tag(self.current_object.id, tag)
        self.update_tags_list()
    
    def open_current_object_location(self):
        """Ouvre l'emplacement de l'objet courant"""
        if self.current_object:
            success = self.current_object.open_location()
            if not success:
                QMessageBox.warning(self, "Erreur", "Impossible d'ouvrir l'emplacement.")
    
    def open_object_location(self, item):
        """Ouvre l'emplacement de l'objet double-cliqué"""
        obj_id = item.data(Qt.UserRole)
        if obj_id in self.db.objects:
            obj = self.db.objects[obj_id]
            success = obj.open_location()
            if not success:
                QMessageBox.warning(self, "Erreur", "Impossible d'ouvrir l'emplacement.")
    
    def show_context_menu(self, position):
        """Affiche le menu contextuel pour la liste des résultats"""
        if not self.results_list.currentItem():
            return
        
        menu = QMenu()
        
        open_action = menu.addAction("Ouvrir l'emplacement")
        edit_action = menu.addAction("Modifier")
        delete_action = menu.addAction("Supprimer")
        
        action = menu.exec_(self.results_list.mapToGlobal(position))
        
        if action == open_action:
            self.open_current_object_location()
        elif action == edit_action:
            self.edit_current_object()
        elif action == delete_action:
            self.delete_current_object()
    
    def show_about(self):
        """Affiche la boîte de dialogue À propos"""
        QMessageBox.about(self, "À propos", 
            "Gestionnaire de Fichiers par Tags\n\n"
            "Une application pour organiser et retrouver vos fichiers à l'aide de tags.\n\n"
            "Fonctionnalités:\n"
            "- Ajout de fichiers locaux ou d'URLs web\n"
            "- Organisation par tags\n"
            "- Recherche avancée\n"
            "- Prévisualisation des fichiers\n"
            "- Interface moderne avec thème sombre/clair"
        )

def main():
    app = QApplication([])
    
    # Configuration initiale
    config = Config()
    
    # Vérifier si c'est le premier démarrage
    if config.is_first_run():
        dialog = FirstRunDialog()
        if dialog.exec_() == QDialog.Accepted:
            data_dir = dialog.get_data_dir()
            config.set_data_dir(data_dir)
            config.set_first_run_complete()
        else:
            # L'utilisateur a annulé, on quitte
            return
    
    # Appliquer le thème
    ThemeManager.apply_theme(app, config.get_theme())
    
    # Créer et afficher la fenêtre principale
    window = MainWindow()
    window.show()
    
    app.exec_()

if __name__ == "__main__":
    main()