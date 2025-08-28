import os
import hashlib
from collections import defaultdict
from pathlib import Path

class DuplicateFinder:
    def __init__(self):
        self.file_groups_by_size = defaultdict(list)
        self.file_groups_by_partial_hash = defaultdict(list)
        self.duplicates = []

    def find_duplicates(self, directory):
        """Méthode principale qui orchestre tout le processus."""
        # Étape 1: Grouper par taille (Niveau 1)
        self._group_files_by_size(directory)

        # Étape 2: Pour les groupes de même taille, grouper par hash partiel (Niveau 2)
        for size, files in self.file_groups_by_size.items():
            if len(files) > 1: # Seulement si potentiel doublon
                self._group_files_by_partial_hash(files)

        # Étape 3: Pour les groupes de même hash partiel, vérifier par hash complet (Niveau 3)
        for partial_hash, files in self.file_groups_by_partial_hash.items():
            if len(files) > 1:
                self._check_full_hashes(files)

        return self.duplicates

    def find_duplicates_from_list(self, file_paths):
        """Nouvelle méthode: trouve les doublons à partir d'une liste de fichiers"""
        # Étape 1: Grouper par taille
        size_groups = defaultdict(list)
        for file_path in file_paths:
            try:
                if os.path.exists(file_path) and not os.path.islink(file_path):
                    size = os.path.getsize(file_path)
                    if size > 0:  # Ignorer les fichiers vides
                        size_groups[size].append(file_path)
            except (OSError, PermissionError):
                continue
        
        # Étape 2: Pour les groupes de même taille, grouper par hash partiel
        partial_hash_groups = defaultdict(list)
        for size, files in size_groups.items():
            if len(files) > 1:
                for file_path in files:
                    try:
                        partial_hash = get_partial_hash(file_path)
                        if partial_hash:
                            partial_hash_groups[partial_hash].append(file_path)
                    except (OSError, PermissionError):
                        continue
        
        # Étape 3: Pour les groupes de même hash partiel, vérifier par hash complet
        final_duplicates = []
        for partial_hash, files in partial_hash_groups.items():
            if len(files) > 1:
                hash_groups = defaultdict(list)
                for file_path in files:
                    try:
                        full_hash = get_full_hash(file_path)
                        if full_hash:
                            hash_groups[full_hash].append(file_path)
                    except (OSError, PermissionError):
                        continue
                
                for file_list in hash_groups.values():
                    if len(file_list) > 1:
                        final_duplicates.append(file_list)
        
        return final_duplicates

    def _group_files_by_size(self, directory):
        """Niveau 1: Groupe tous les fichiers par leur taille."""
        for root, dirs, files in os.walk(directory):
            for file in files:
                path = Path(root) / file
                try:
                    # Ignorer les fichiers vides et les liens symboliques
                    if path.is_symlink() or path.stat().st_size == 0:
                        continue
                    size = path.stat().st_size
                    self.file_groups_by_size[size].append(path)
                except (OSError, PermissionError):
                    continue  # Ignorer les fichiers inaccessibles

    def _group_files_by_partial_hash(self, files):
        """Niveau 2: Groupe les fichiers par leur hash partiel."""
        for file_path in files:
            try:
                partial_hash = get_partial_hash(file_path)
                self.file_groups_by_partial_hash[partial_hash].append(file_path)
            except (OSError, PermissionError):
                continue  # Ignorer les fichiers inaccessibles

    def _check_full_hashes(self, files):
        """Niveau 3: Compare les hashs complets et enregistre les doublons."""
        hash_groups = defaultdict(list)
        for file_path in files:
            try:
                full_hash = get_full_hash(file_path)
                hash_groups[full_hash].append(file_path)
            except (OSError, PermissionError):
                continue  # Ignorer les fichiers inaccessibles

        for file_list in hash_groups.values():
            if len(file_list) > 1:
                self.duplicates.append(file_list) # On ajoute la liste des doublons

def get_partial_hash(file_path, chunk_size=1024*1024): # 1 Mo
    """Calcule le hash partiel du fichier (premier Mo)"""
    hash_func = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(chunk_size)
            if chunk:
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except (OSError, PermissionError):
        return ""  # Retourner une chaîne vide en cas d'erreur

def get_full_hash(file_path, chunk_size=8192):
    """Calcule le hash complet du fichier"""
    hash_func = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except (OSError, PermissionError):
        return ""  # Retourner une chaîne vide en cas d'erreur