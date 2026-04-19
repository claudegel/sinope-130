# Neviweb130 – Intégration Home Assistant pour les appareils Sinopé

L’intégration **Neviweb130** permet de connecter les appareils Sinopé utilisant la plateforme **Neviweb** et les passerelles **GT130** à Home Assistant.  
Elle offre une gestion avancée, une grande stabilité, et une compatibilité étendue avec les appareils Zigbee Sinopé.

Cette intégration est une évolution majeure du projet original, avec une architecture modernisée, une meilleure gestion des erreurs, une migration facilitée et une documentation complète.

---

# 🚀 Fonctionnalités principales

- Connexion directe à la plateforme **Neviweb** (API officielle)
- Support des appareils Sinopé Zigbee via **GT130**
- Mise à jour automatique des entités
- Gestion avancée des thermostats, interrupteurs, gradateurs, contrôleurs de charge, etc.
- Migration automatique des anciens `unique_id` numériques
- Options avancées de journalisation et diagnostics
- Support multi‑comptes Neviweb
- Compatibilité avec les sauvegardes Home Assistant
- Détection automatique des nouveaux appareils

---

# 🧩 Appareils supportés

### Thermostats
- TH1123ZB / TH1124ZB
- TH1300ZB (plancher chauffant)
- TH1400ZB (eau chaude)

### Interrupteurs et gradateurs
- SW2500ZB
- DM2500ZB
- RM3250ZB

### Contrôleurs de charge
- RM3500ZB
- RM3500RF

### Passerelles
- GT130 (Zigbee)

### Et plusieurs autres modèles Sinopé Zigbee

> La liste complète est disponible dans la documentation du dossier `docs/`.

---

# 📦 Installation

## 🔹 Via HACS (recommandé)

1. Ouvrez **HACS → Intégrations**
2. Cliquez sur **Custom repositories**
3. Ajoutez :  
   `https://github.com/claudegel/sinope-130`
4. Catégorie : **Integration**
5. Installez **Neviweb130**
6. Redémarrez Home Assistant

## 🔹 Installation manuelle

1. Téléchargez la dernière version depuis GitHub
2. Copiez le dossier `custom_components/neviweb130` dans :
3. Redémarrez Home Assistant

---

# ⚙️ Configuration initiale

1. Allez dans **Paramètres → Appareils et services**
2. Cliquez sur **Ajouter une intégration**
3. Recherchez **Neviweb130**
4. Entrez vos identifiants Neviweb
5. Sélectionnez votre passerelle GT130 si nécessaire
6. Attendez la découverte automatique des appareils

---

# 🔧 Options avancées

L’intégration propose plusieurs options configurables :

### Préfixe du compte
Permet de distinguer plusieurs comptes Neviweb dans Home Assistant.

### Niveau de journalisation
- debug  
- info  
- warning  
- error  
- critical  

### Taille maximale du journal
Limite en octets avant rotation.

### Nombre de fichiers de sauvegarde
Nombre de logs conservés.

### Réinitialisation du journal au démarrage
Efface le fichier log au redémarrage de l’intégration.

### Télécharger les diagnostics
Génère un fichier ZIP contenant :
- logs
- configuration
- informations système

### Recharger l’intégration
Recharge sans redémarrer Home Assistant.

### Migrer les `unique_id` numériques
Convertit les anciens identifiants en format textuel stable.

### Mode de sauvegarde
- full  
- partial  

### Répertoire racine de la sauvegarde
Chemin du dossier à sauvegarder.

Pour plus de détails :  
➡️ `docs/options.md`

---

# 🔄 Reconfiguration

Vous devez reconfigurer l’intégration si :

- vous changez votre mot de passe Neviweb  
- vous ajoutez un nouveau compte  
- vous modifiez votre réseau Zigbee  
- vous remplacez un GT130  
- vous rencontrez des erreurs d’authentification  

Procédure complète :  
➡️ `docs/reconfigure.md`

---

# 🧩 Ajouter un nouveau bridge GT130

L’intégration supporte plusieurs passerelles GT130.

Procédure complète :  
➡️ `docs/new_bridge.md`

---

# 🛠️ Dépannage

### Aucun appareil détecté
- Vérifiez que votre GT130 est en ligne dans Neviweb
- Vérifiez vos identifiants
- Redémarrez Home Assistant

### Les entités ne se mettent pas à jour
- Vérifiez la connectivité Internet
- Vérifiez le polling dans les logs
- Activez le niveau `debug` pour plus d’informations

### Problèmes de migration
- Utilisez l’option **Migrer les unique_id numériques**
- Consultez les logs pour les identifiants problématiques

---

# 📝 Journalisation et diagnostics

L’intégration inclut un système de logs avancé :

- rotation automatique
- taille configurable
- téléchargement des diagnostics
- messages détaillés pour le support

---

# 📚 Documentation complète

Toute la documentation est disponible dans le dossier :


Index :  
➡️ `docs/doc_index.md`

---

# 🤝 Contribution

Les contributions sont les bienvenues :

- corrections
- améliorations
- nouveaux appareils
- documentation

Ouvrez une *issue* ou une *pull request* sur GitHub.

---

# 📄 Licence

Ce projet est distribué sous licence MIT.

---

# 🙏 Remerciements

Merci à la communauté Home Assistant et aux utilisateurs qui ont contribué à améliorer cette intégration au fil des années.
