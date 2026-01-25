## Home Assistant Neviweb130 Custom Components
[🇬🇧 English version](../README.md)
> 💛 **Vous aimez cette integration?**  
> Si vous voulez supporter son développement, vous pouvez contribuer ici:
> [![Support via PayPal](https://cdn.rawgit.com/twolfson/paypal-github-button/1.0.0/dist/button.svg)](https://www.paypal.me/phytoressources/)

Composants personnalisés pour prendre en charge les appareils [Neviweb](https://neviweb.com/) dans [Home Assistant](http://www.home-assistant.io) (HA). 
Neviweb est une plateforme créée par Sinopé Technologies pour interagir avec leurs appareils intelligents comme les thermostats, l'éclairage
interrupteurs/gradateurs, contrôleurs de charge, prise, vannes et détecteur de fuite d'eau, etc.

Neviweb130 gérera les appareils Zigbee connectés à Neviweb via la passerelle GT130 et les nouveaux appareils Wi-Fi connectés 
directement sur Neviweb. Il est actuellement pratiquement à jour avec Neviweb mais certaines informations manquent encore chez Sinopé. 
Au fur et à mesure que de nouveaux appareils sont lancés par Sinopé, ils sont ajoutés à ce composant personnalisé. Si vous possédez 
un appareil qui n'est pas pris en charge, veuillez ouvrir une issue et je l'ajouterai rapidement.

Signaler un problème ou proposer une amélioration : [Créer une issue](https://github.com/claudegel/sinope-130/issues/new/choose)

## Gros changements pour les valves Sedna

Depuis la version de neviweb130 2.6.2, les valves sont pris en charge en tant que nouvelles entités de valve dans HA. Ils ne sont plus pris 
en charge en tant que commutateur (switch). Ceci entraîne le remplacement de toutes vos entités `switch.neviweb130_switch_sedna_valve` par 
des entités `valve.neviweb130_valve_sedna_valve`. Vous devrez réviser vos automatismes et vos cartes pour récupérer vos entités valves.

## Appareils pris en charge:
Voici une liste des appareils actuellement pris en charge. En gros, c'est tout ce qui peut être ajouté dans Neviweb.
- **thermostats Zigbee**:
  - Sinopé TH1123ZB, thermostat de ligne 3000W
  - Sinopé TH1124ZB, thermostat de ligne 4000W
  - Sinopé TH1123ZB, thermostat de ligne pour aires publiques 3000W
  - Sinopé TH1124ZB, thermostat de ligne pour aires publiques 4000W
  - Sinopé TH1123ZB-G2, thermostat deuxième génération 3000W
  - Sinopé TH1124ZB-G2, thermostat deuxième génération 4000W
  - Sinopé TH1134ZB-HC, pour le contrôle du verrouillage chauffage/refroidissement
  - Sinopé TH1300ZB, thermostat de chauffage au sol 3600W
  - Sinopé TH1320ZB-04, thermostat de chauffage au sol
  - Sinopé TH1400ZB, thermostat basse tension
  - Sinopé TH1500ZB, thermostat bipolaire 3600W
  - Nordik TH1420ZB-01, thermostat de plancher hydroponique radiant basse tension Nordik
  - Ouellet OTH3600-GA-ZB, thermostat de plancher Ouellet
  - Ouellet OTH4000-ZB, thermostat basse tension Ouellet 4000W
- **thermostats Wi-Fi** (pas besoin de GT130):
  - Sinopé TH1124WF Wi-Fi, thermostat de ligne 4000W
  - Sinopé TH1123WF Wi-Fi, thermostat de ligne 3000W
  - Sinopé TH1133WF Wi-Fi, thermostat à tension de ligne – édition Lite 3000W
  - Sinopé TH1133CR, thermostat à tension de ligne – édition Lite Sinopé Evo 3000w
  - Sinopé TH1134WF Wi-Fi, thermostat à tension de ligne – édition Lite 4000W
  - Sinopé TH1134CR, Thermostat à tension de ligne – édition Lite Sinopé Evo 4000w
  - Sinopé TH1143WF, thermostat à deux fils, écran couleur Wi-Fi 3000W
  - Sinopé TH1144WF, thermostat à deux fils, écran couleur WI-Fi 4000W
  - Sinopé TH1300WF, thermostat au sol Wi-Fi 3600W
  - Sinopé TH1310WF, thermostat au sol Wi-Fi 3600W
  - Sinopé TH1325WF, thermostat au sol Wi-Fi 3600W
  - Sinopé TH1400WF, thermostat basse tension Wi-Fi 
  - Sinopé TH1500WF, thermostat bipolaire Wi-Fi 3600W 
  - Sinopé TH6500WF, thermostat Wi-Fi chauffage/climatisation
  - Sinopé TH6510WF, thermostat Wi-Fi chauffage/climatisation
  - Sinopé TH6250WF, thermostat Wi-Fi chauffage/climatisation
  - Sinopé TH6250WF_PRO, thermostat Wi-Fi chauffage/climatisation PRO
  - Sinopé THEWF01, thermostat de ligne, édition lite Wi-Fi
  - Flextherm concerto connect FLP55 thermostat de sol (sku FLP55 ne fourni pas de statistique énergétique dans Neviweb)
  - Flextherm True Comfort, thermostat de sol
  - SRM40, thermostat de sol
- **Contrôleur de pompe à chaleur**:
  - Sinopé HP6000ZB-GE, pour les thermopompes Ouellet avec connecteur Gree
  - Sinopé HP6000ZB-MA, pour les thermopompes Ouellet, Convectair avec connecteur Midea
  - Sinopé PH6000ZB-HS, pour les thermopompes Hisense, Haxxair et Zephyr
- **Contrôleur de pompe à chaleur Wi-Fi**:
  - Sinopé HP6000WF-MA, pour les thermopompes Ouellet, Convectair avec connecteur Midea
  - Sinopé HP6000WF-GE, pour les thermopompes Ouellet avec connecteur Gree
- **éclairage Zigbee**:
  - Sinopé SW2500ZB, Interrupteur
  - Sinopé SW2500ZB-G2, Interrupteur nouvelle génération
  - Sinopé DM2500ZB, gradateur
  - Sinopé DM2500ZB-G2, gradateur nouvelle génération
  - Sinopé DM2550ZB, gradateur
  - Sinopé DM2550ZB-G2, gradateur
- **Contrôle spécialisé Zigbee**:
  - Sinopé RM3250ZB, Contrôleur de charge 50A
  - Sinopé RM3500ZB, Contrôleur de charge Calypso pour chauffe-eau 20,8A 
  - Sinopé SP2610ZB, prise murale
  - Sinopé SP2600ZB, prise portable intelligente
  - Sinopé MC3100ZB, multicontrôleur pour système d'alarme et valve Sedna
- **Contrôle spécialisé Wi-Fi**:
  - Sinopé RM3500WF, Contrôleur de charge pour chauffe-eau, Wi-Fi
  - Sinopé RM3510WF, Contrôleur de charge pour chauffe-eau, Wi-Fi
  - Sinopé RM3250WF, Contrôleur de charge 50A, Wi-Fi
- **Water leak detector and valves**:
  - Sinopé VA4201WZ, VA4221WZ, valve sedna 1 pouce
  - Sinopé VA4200WZ, VA4220WZ, valve sedna 3/4 pouce, Wi-Fi
  - Sinopé VA4200ZB, valve sedna 3/4 pouce Zigbee
  - Sinopé VA4220WZ, valve sedna 2e gen 3/4 pouce
  - Sinopé VA4220WF, valve sedna 2e gen 3/4 pouce, Wi-Fi
  - Sinopé VA4220ZB, valve sedna 2e gen 3/4 pouce, Zigbee
  - Sinopé VA4221WZ, valve sedna 2e gen 1 pouce
  - Sinopé VA4221WF, valve sedna 2e gen 1 pouce, Wi-Fi
  - Sinopé VA4221ZB, valve sedna 2e gen 1 pouce, Zigbee
  - Sinopé WL4200,   détecteur de fuite
  - Sinopé WL4200S,  détecteur de fuite avec sonde déportée
  - Sinopé WL4200C,  cable de périmètre détecteur de fuite
  - Sinopé WL4200ZB, détecteur de fuite
  - Sinopé WL4210,   détecteur de fuite
  - Sinopé WL4210S,  détecteur de fuite avec sonde déportée
  - Sinopé WL4210C,  cable de périmètre détecteur de fuite
  - Sinopé WL4210ZB, détecteur de fuite
  - Sinopé WL4200ZB, détecteur de fuite connecté à la valve Sedna
  - Sinopé ACT4220WF-M, VA4220WF-M, valve sedna multi-residentiel maitre valve 2e gen 3/4 pouce, Wi-Fi
  - Sinopé ACT4220ZB-M, VA4220ZB-M, valve sedna multi-residentiel secondaire valve 2e gen 3/4 pouce, Zigbee
  - Sinopé ACT4221WF-M, VA4221WF-M, valve sedna multi-residentiel maitre valve 2e gen. 1 pouce, Wi-Fi
  - Sinopé ACT4221ZB-M, VA4221ZB-M, valve sedna multi-residentiel secondaire valve 2e gen. 1 pouce, Zigbee
- **Capteur de débit**: (pris en charge comme attribut pour les valves Sedna de 2e génération)
  - Sinopé FS4220, capteur de débit 3/4 pouce
  - Sinopé FS4221, capteur de débit 1 pouce
- **Moniteur de niveau de réservoir**:
  - Sinopé LM4110-ZB, Moniteur de niveau de réservoir de propane
  - Sinopé LM4110-LTE, Moniteur de niveau de réservoir de propane LTE
- **Passerelle**:
  - GT130
  - GT4220WF-M, passerelle mesh
- **Alimentation**:
  - Sinopé ACUPS-01, batterie de secours pour valve Sedna, GT130 ou GT125
 
## Prérequis
Vous devez connecter vos appareils à une passerelle Web GT130 et les ajouter dans votre portail Neviweb avant de pouvoir 
interagir avec eux dans Home Assistant. Pour les appareils Wi-Fi vous devez les connecter directement à Neviweb. Veuillez
vous référer au manuel d'instructions de votre appareil ou visiter [Assistance Neviweb](https://support.sinopetech.com/)

Les appareils Wi-Fi peuvent être connectés au même réseau (emplacement) que les appareils GT130 Zigbee ou dans un réseau séparé.
**Neviweb130** supporte jusqu'à trois réseaux dans Neviweb.

Il existe deux composants personnalisés vous donnant le choix de gérer vos appareils via le portail neviweb ou directement en local. 

**Passerelle Zigbee**:
- [Neviweb130](https://github.com/claudegel/sinope-130) ce composant personnalisé, pour gérer vos appareils via le portail Neviweb.
- [sinope-zha](https://github.com/claudegel/sinope-zha) où je mets tous les gestionnaire d’adaptations Zigbee (quirks) des nouveaux
  appareils Sinopé avant qu'ils ne soient fusionnés dans les gestionnaires de périphériques ZHA. Achetez une passerelle Zigbee
  comme la clé USB **Dresden ConBee II** et gérez votre appareil Zigbee localement via le composant ZHA. J'ajoute le support des
  appareils Sinopé Zigbee dans le gestionnaire de périphériques ZHA. Vous pouvez tester les gestionnaire d’adaptations Zigbee
  Sinopé dans HA en copiant les fichiers sinope-zha directement dans votre configuration HA. ZHA les chargera à la place des
  gestionnaire d’adaptations Zigbee standard de Sinopé dans ZHA.

Vous pouvez en installer qu’un seul, mais les deux peuvent être utilisés en même temps sur HA. Les appareils Zigbee gérés directement via 
ZHA doivent être supprimées de Neviweb car elles ne peuvent pas être sur deux réseaux Zigbee en même temps.

## Composant personnalisé Neviweb130 pour gérer votre appareil via le portail Neviweb :
##Installation
Il existe deux méthodes pour installer ce composant personnalisé :
- **Via le composant HACS** (Home Assistant Community Store):
  - Neviweb130 est compatible avec [HACS](https://community.home-assistant.io/t/custom-component-hacs/121727).
  - Après avoir installé HACS, installez « Sinope neviweb-130 » (neviweb130) depuis le magasin et utilisez l'exemple configuration.yaml ci-dessous.
- **Manuellement via téléchargement direct**:
  - Téléchargez le fichier zip de ce référentiel en utilisant le bouton de téléchargement vert en haut à droite.
  - Extrayez le fichier zip sur votre ordinateur, puis copiez l'intégralité du dossier « custom_components » dans votre Home Assistant 
    Répertoire `config` (où vous pouvez trouver votre fichier `configuration.yaml`).
  - Votre répertoire de configuration devrait ressembler à ceci :
 
   ```
    config/
      configuration.yaml
      custom_components/
        neviweb130/
          __init__.py
          climate.py
          const.py
          helpers.py
          light.py
          manifest.json
          schema.py
          sensor.py
          services.yaml
          switch.py
          update.py
          valve.py
    ```
## Configuration 1er génération

Pour activer la gestion Neviweb130 dans votre installation, ajoutez ce qui suit à votre fichier `configuration.yaml`, puis redémarrez 
Home Assistant.

```yaml
# Exemple d'entrée dans configuration.yaml 
neviweb130:
  username: '«your Neviweb username»'
  password: '«your Neviweb password»'
  network: '«your gt130 location name in Neviweb»'   # gt130 emplacement dans Neviweb
  network2: '«your second location name in Neviweb»' # 2e emplacement
  network3: '«your third location name in Neviweb»'  # 3e emplacement
  scan_interval: 360
  homekit_mode: False
  ignore_miwi: False
  stat_interval: 1800
  notify: "both"
```
Les noms de réseaux sont les noms trouvés en haut de la première page après la connexion à Neviweb. Si vous disposez de plusieurs réseaux, 
cliquez simplement sur l'icône en haut pour trouver tous les noms de réseaux. Sélectionnez celui utilisé pour les appareils Zigbee GT130 ou Wi-Fi.
Les deux types d'appareils peuvent être sur le même réseau pour fonctionner dans neviweb130 ou sur des réseaux séparés. Si vous disposez de deux 
réseaux pour deux GT130 ou deux groupes Wi-Fi, vous pouvez ajoutez le paramètre network2 dans votre configuration.yaml. Voir ci-dessous. 
Vous ne pouvez pas mélanger des appareils Miwi et des appareils Zigbee/Wi-Fi sur le même réseau. Pour les appareils miwi, installez [Neviweb](https://github.com/claudegel/sinope-1) 
custom_component qui peut s'exécuter avec ce custom_component dans HA.

![network](www/network.jpg)

**Options de configuration:**  

| clé               | requis | défaut                                                                                                            | description                                                                                                                                                                                                                  |
|-------------------|----------|--------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **username**      | Oui      |                                                                                                                    | Votre adresse email utilisée pour vous connecter à Neviweb.                                                                                                                                                                                 |
| **password**      | Oui      |                                                                                                                    | le mot de passe de votre compte Neviweb.                                                                                                                                                                                                       |
| **network**       | non      | s'il n'est pas spécifié, le 1er emplacement trouvé est utilisé. Écrivez le nom de l'emplacement GT130 dans Neviweb que vous souhaitez contrôler. | Le nom du réseau est le nom de l'emplacement dans Neviweb écrit en haut au centre de la première page, où vos appareils Wi-Fi ou Zigbee sont enregistrés.                                                                                         |
| **network2**      | non      | 2nd réseaux (emplacement) trouvé                                                                                   | Le nom du deuxième emplacement que vous souhaitez contrôler (Zigbee et/ou Wi-Fi uniquement). Ne l'ajoutez pas si vous n'avez qu'un seul réseau.                                                                                                 |
| **network3**      | non      | 3rd réseaux (emplacement) trouvé                                                                                   | Le nom du troisième emplacement que vous souhaitez contrôler (Zigbee et/ou Wi-Fi uniquement). Ne l'ajoutez pas si vous n'avez qu'un seul réseau.                                                                                             |
| **scan_interval** | non      | 540                                                                                                                | Le nombre de secondes entre chaque accès à Neviweb pour mettre à jour l'état de l'appareil. Sinopé a maintenant demandé un minimum de 5 minutes entre les interrogations afin que vous puissiez réduire scan_interval à 300. Ne dépassez pas 600, la session expirera. |
| **homekit_mode**  | non      | False                                                                                                              | Ajoutez la prise en charge des valeurs spécifiques à Homekit. Pas nécessaire si vous n'utilisez pas homekit.                                                                                                                                               |
| **ignore_miwi**   | non      | False                                                                                                              | Ignorez les appareils Miwi s'ils sont présents au même endroit que les appareils Zigbee et/ou Wi-Fi. Réchauffez-vous si nous définissons un mauvais emplacement Neviweb.                                                                                                   |
| **stat_interval** | non      | 1800                                                                                                               | Le nombre de secondes entre chaque accès à Neviweb pour la mise à jour des statistiques énergétiques. L'analyse démarrera 5 minutes après le démarrage de HA et sera mise à jour toutes les 300 à 1 800 secondes.                                          |
| **notify**        | non      | both                                                                                                               | La méthode pour envoyer une notification en cas d'erreur de périphérique. L'option de valeur est `nothing`, `logging`, `notification`, `both`.                                                                                                              |

Si vous avez un GT125 également connecté à Neviweb, le paramètre réseau est obligatoire, ou il est possible que lors de la 
configuration, le réseau du GT125 sera capté accidentellement. Si vous ne disposez que de deux réseaux GT130/Wi-Fi, vous pouvez omettre leurs
noms comme lors de la configuration, les deux premiers réseaux trouvés seront automatiquement récupérés. Si vous préférez ajouter des noms de réseaux 
assurez-vous qu'ils soient écrits « exactement » comme dans Neviweb. (première lettre majuscule ou non). Évitez également les lettres accentuées 
car Home Assistant les supprimera et le nom de l'emplacement ne correspondra pas, empêchant le chargement de custom_component.

## Configuration multi-comptes (nouveau dans la version 3.1.0)

Si vous devez contrôler des appareils à partir de **plusieurs comptes Neviweb** (par exemple, votre maison et celle d'un voisin), vous pouvez 
désormais utiliser le nouveau format de configuration multi-comptes. Cela élimine le besoin de dupliquer le dossier des composants personnalisés.

```yaml
# Exemple de configuration multi-comptes
neviweb130:
  accounts:
    # Compte avec plusieurs emplacements (ex: maison et chalet)
    - username: 'your_email@example.com'
      password: 'your_password'
      # l'emplacement (location) était appelé réseau dans les versions précédentes.
      #
      # Optionel: vous pouvez cibler jusqu'à trois emplacements pour ce compte:
      #   location / location2 / location3 (ou network / network2 / network3)
      #
      # Si vous omettez tous les emplacements, l'intégration utilisera automatiquement les 1 à 3 premiers emplacements
      # retourné par Neviweb pour ce compte.
    
    # Compte séparé pour les parents (en utilisant `network` - fonctionne de la même manière que `location`)
    - username: 'parents_email@example.com'
      password: 'parents_password'
      location: '5678'           # Optionel: location id/name (ou utiliser 'network')
      prefix: 'parents'          # Optionel: pseudonyme de compte (utilisé dans la dénomination des entités)
  
  # Paramètres globaux (s'appliquent à tous les comptes)
  scan_interval: 360
  homekit_mode: False
  ignore_miwi: False
  stat_interval: 1800
  notify: "both"
```
Les paramètres sont en anglais. Il ne faut pas les traduire.

> **⚠️ Important : Conflits de noms d'entité dans la configuration multi-comptes**
> 
> Les noms d'entités sont construits à partir du domaine d'intégration (`neviweb130`), plus des valeurs facultatives de `prefix` et/ou `location` (emplacement).
> 
> **Problème :** Si vous omettez à la fois « préfixe » et « emplacement » pour plusieurs comptes et que les deux comptes ont des appareils avec des noms
> similaires (par exemple, les deux ont un thermostat appelé « LivingRoom »), Home Assistant peut suffixer automatiquement les identifiants d'entité :
> - `climate.neviweb130_livingroom`
> - `climate.neviweb130_livingroom_2` ← Collision gérée par HA
> 
> **Solution :** Fournissez soit un « préfixe » unique (alias de compte), soit des noms/identifiants d'« location » (emplacement) explicites, pour que les
> identifiants d'entité restent stables et lisibles :
> ```yaml
> accounts:
>   - username: 'user1@example.com'
>     password: 'pass1'
>     location: 'Home'
>     prefix: 'me'          # ← account alias
>   - username: 'user2@example.com'
>     password: 'pass2'
>     location: 'Chalet'
>     prefix: 'parents'     # ← different account alias
> ```
> Example: `climate.neviweb130_parents_chalet_climate_livingroom`.

**Options de configuration Multi-comptes:**

| clé | requis | défaut | description
| --- | --- | --- | ---
| **accounts** | oui (pour multi-comptes) | | Liste des comptes auxquels se connecter
| **username** | oui | | Votre adresse email pour ce compte Neviweb
| **password** | oui | | Le mot de passe de ce compte Neviweb
| **location** (ou **network**) | non | premier emplacement trouvé | Identifiant/nom d'emplacement pour ce compte (réseau n° 1).
| **location2** (ou **network2**) | non | deuxième emplacement trouvé | Identifiant/nom d'emplacement pour ce compte (réseau n° 2).
| **location3** (ou **network3**) | non | troisième emplacement trouvé | Identifiant/nom d'emplacement pour ce compte (réseau n° 3).
| **prefix** | non | (vide) | Alias ​​de compte facultatif utilisé dans la dénomination de l’entité pour distinguer les comptes.

**Notes:**
- `préfixe` est facultatif. S'il est omis, il n'est pas inclus dans le nom de l'entité (Home Assistant peut suffixer automatiquementent
  les entités si des collisions se produisent).
- Si les noms/identifiants de votre « emplacement » sont déjà uniques dans vos comptes (par exemple, vous utilisez une adresse, un code
  de site ou une autre étiquette unique), vous pouvez omettre entièrement le « préfixe » et vous fier à « l'emplacement » pour distinguer
  les entités.
- Chaque compte maintient sa propre connexion indépendante à Neviweb.
- **Plusieurs emplacements par compte**:
  - Si vous omettez tous les emplacements, l'intégration utilisera automatiquement les 1 à 3 premiers emplacements renvoyés par Neviweb.
  - Ou vous pouvez définir explicitement « location2 » et « location3 ».
- "location*" et "network*" sont tous deux acceptés comme alias dans le nouveau format par souci de cohérence avec l'ancien format.
- Les paramètres globaux (`scan_interval`, `homekit_mode`, etc.) s'appliquent à tous les comptes.
- L'ancien format de configuration à compte unique (illustré ci-dessus) reste entièrement pris en charge pour une compatibilité ascendante.

**Exemple de nom d'entité:**
- **Ancienne configuration à compte unique (dénomination rétrocompatible)**:
  - 1er emplacement → `climate.neviweb130_climate_room`
  - 2ème emplacement → `climate.neviweb130_climate_2_room`
  - 3ème emplacement → `climate.neviweb130_climate_3_room`
- **Configuration multi-comptes (`comptes :`)**:
  - Avec préfixe + localisation → `climate.neviweb130_parents_chalet_climate_living_room`
  - Avec localisation uniquement (pas de préfixe) → `climate.neviweb130_chalet_climate_living_room`

## Valve Sedna
Pour les valves Sedna, il existe deux façons de les connecter à Neviweb :
- Via connexion Wi-Fi directe. De cette façon, les capteurs de fuite sont connectés directement à la valve Sedna qui se fermera en cas de fuite. 
- via GT130 en mode Zigbee. De cette façon, les capteurs de fuite sont également connectés au GT130 mais lors de la détection de fuite,
  rien transmis à la valve. Vous devrez définir une règle d'automatisation dans Neviweb ou HA, pour que la valve Sedna se ferme en cas de fuite 
  détecté par le capteur.

Les deux modes sont pris en charge par ce composant personnalisé.

## Passerelle GT130
Il est désormais possible de savoir si votre GT130 est toujours en ligne ou hors ligne avec Neviweb via l'attribut gateway_status. Le 
GT130 est détecté comme sensor.neviweb130_sensor_gt130

## Programme de mise à jour

Neviweb130 inclut désormais un système de mise à jour complet qui comprend :
- Vérification automatique des mises à jour toutes les 6 heures :
  - Nouvelle mise à jour disponible.
  - Pré-version disponible.
  - Changements cassants. (breaking changes)
  - Notes de version.

-Validation SHA-256 :
  - Valide le zip SHA-256 officiel sur GitHub.
  - Télécharge le fichier zip de mise à jour.
  - Valide le SHA-256.
  - En cas de discordance, annule la mise à jour et envoi une notification.

- Restauration automatique si une erreur est détectée lors de la mise à jour :
  - Restaure automatiquement l'ancienne version.
  - Informe l'utilisateur du problème via une notification.
 
- Notifications persistantes sur :
  - Succès : "Mise à jour réussie".
  - Échec : "Échec de la mise à jour, restauration effectuée".
  - Erreur SHA-256 : "Mise à jour interrompue pour des raisons de sécurité".

- Détection des modifications avec rupture (breaking changes) :
  Les notes de version de l'analyse du programme de mise à jour proviennent de GitHub. Si des modifications avec rupture sont détectées :
  - Ajoute une icône spéciale dans la carte de mise à jour.
  - Ajoute (breaking changes) dans le titre du programme de mise à jour.
 
- Détection de version préliminaire si la version contient, b0, -beta ou rc1 etc :
  La version de mise à jour de l'analyse du programme de mise à jour depuis GitHub. Si une version préliminaire est détectée :
  - Ajouter une icône spéciale dans la carte de mise à jour.
  - Ajouter (Pre-release) dans le titre du programme de mise à jour.

- Option de sauvegarde :
  Ajoute un bouton pour activer la sauvegarde du système avant la mise à jour. Tout le répertoire de configuration (config) et la base
  de données sont sauvegardés.

- Les notes de version peuvent être consultées via le lien fourni sur la carte de mise à jour qui pointe vers les versions de GitHub.

- Le programme de mise à jour possède de nombreux attributs pour aider l'utilisateur :
  - check_interval: 6h, (deviendra une option dans la prochaine version de Neviweb130-V2)
  - last_check : date/heure de la dernière vérification de version disponible.
  - next_check : date/heure de la prochaine vérification de version disponible.
  - last_update_success : date/heure de la dernière mise à jour.
  - update_status : liste toutes les étapes effectuées lors de la mise à jour.
  - rollback_status : si une mise à jour échoue, la dernière version active sera restaurée.
  - update_percentage : Afficher un curseur pour le suivi du processus de mise à jour.

Vous devrez désactiver la mise à jour HACS ou vous recevrez deux notifications de mise à jour avec deux cartes de mise à jour. 
Cela peut être fait dans paramètres / appareils et services / HACS. Choisissez 'Sinope Neviweb130' et desactuiiver l'option pre-release.
Puis et cliquer sur le menu 3-points à l'extrémité droite de la ligne. Dans ce menu il y a une sélection 2 entité. Ouvrir cet option 
et chosir Update. Il sera toujours possible de faire une mise a jour ou retélécharger une autre version via HACS.

Vous pouvez aussi attendre une nouvelle mise a jour, ouvrir la carte de HACS et cliquer sur la molette de configuration.
Désactiver l'option `Visible`.

## Compteur de requêtes quotidiennes Neviweb
Comme Sinopé est de plus en plus pointilleux sur le nombre de requêtes par jour, la limite est fixée à 30000. Si vous atteignez cette limite, vous 
serez déconnecté jusqu'à minuit. C'est très mauvais si vous possédez de nombreux appareils ou si vous développez sur neviweb130.
J'ai ajouté un compteur de requêtes Neviweb quotidien qui est réinitialisé à 0 à minuit et qui survit à un  redémarrage de HA. Cela crée un 
sensor `sensor.neviweb130_daily_requests` qui augmentent à chaque requête : mise à jour, interrogation des statistiques, statut d'erreur, etc.
Le capteur survit au redémarrage de HA et est remis à 0 à minuit tous les soirs.

De cette façon, il est possible d'améliorer votre `scan_interval` pour obtenir la fréquence la plus élevée sans dépasser la limite.
Lorsqu'il atteint 25 000 requêtes, neviweb130 enverra une notification. A terme, cette limite d'avertissement sera configurable.

## Exécution de plusieurs instances de neviweb130 pour gérer différents comptes Neviweb.
> Cette section fonctionne toujours mais comme Neviweb130 prend désormais directement en charge le multi-compte, elle devient obsolète.

