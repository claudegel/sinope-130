# Options de l’intégration Neviweb130

Cette page décrit en détail chaque option disponible dans l’intégration **Neviweb130**.

---

## 🔧 Paramètres disponibles

### **Nom du compte Neviweb (prefix)**
Identifiant unique utilisé pour distinguer plusieurs comptes Neviweb dans Home Assistant.

### **Niveau de journalisation (log_level)**
Définit la quantité d’information enregistrée dans les logs :
- debug
- info
- warning
- error
- critical

### **Taille maximale du journal (log_max_bytes)**
Taille maximale du fichier de log avant rotation.

### **Nombre de fichiers de sauvegarde (log_backup_count)**
Nombre de fichiers de log conservés lors de la rotation.

### **Réinitialisation du journal au démarrage**
Efface le fichier de log au redémarrage de l’intégration.

### **Télécharger les diagnostics**
Permet de télécharger un fichier ZIP contenant les logs et informations utiles pour le support.

### **Recharger l’intégration**
Recharge l’intégration sans redémarrer Home Assistant.

### **Migrer les unique_id numériques**
Convertit les anciens identifiants numériques en identifiants textuels plus stables.

### **Mode de sauvegarde**
- **full** : sauvegarde complète
- **partial** : sauvegarde ciblée

### **Répertoire racine de la sauvegarde**
Chemin du dossier à sauvegarder.

---

## 📘 Voir aussi
- [Index de la documentation](doc_index.md)
