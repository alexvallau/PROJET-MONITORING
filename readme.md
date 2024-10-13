# Développement d'un logiciel de supervision

Dans le cadre de notre projet, il nous a été demandé de développer une application nous permettant de récupérer le nombre d'octets entrants/sortant d'une interface d'une ou plusieurs machines.
Au sein de ce readme vous trouverez essentiellement:
* Comment nous nous sommes organisés et pourquoi
* Un résumé technique de notre application

## Partie organisationnelle

### Résumé général de l'application
Avant de nous lancer dans le développement à proprement parlé, il nous a été recommandé de réfléchir précisément à l'application que nous voulions développer. Au cours de cette phase nous devions: 
* Imaginer un projet concret
* Réfléchir à tout ce qu'engendre ce projet en terme de technicité

Nous vous proposons ici une description des fonctionnalités que doit être capable de fournir notre programme.

Notre application sera un site web, depuis lequel nous pourrons:
* Consulter l(les)'interface de chacun des appareils que nous avons choisi de monitorer. Nous entendons ici: observer le flux entrant et sortant d'une interface selon le temps.
* Pouvoir ajouter/supprimer un appareil à monitorer depuis l'interface web
* Récupération des logs de l'appareil(à définir)
* Voir si une machine est en ligne ou non
* Selon l'utilisateur avec lequel nous nous connectons, différentes possibilités se présenteront


### Choix des technologies

Vous trouverez ci-dessous le choix justifié de nos technologies:

#### Page web
Nous utiliserons flask qui est une librairie de python. Il en existe d'autre mais c'est la technologie que nous maitrisons le mieux pour le web.

#### SNMP
Nous utiliserons pysnmp qui est une librarie python permettant de faire des requêtes SNMP vers des clients. Bien qu'il en existe d'autres en python, cette technologie semble être la plus documentée.

#### Affichage des données
Pour l'instant nous choisissons JS chart qui est une librarie javascript permettant d'afficher divers types de graphique en temps réel.

#### Stockage des données
Etant donnée que ce projet n'est pas d'une "grande" complexité en termes des données à enregistrer, nous avons décidé de stocker les données sous le format json suivant.

```json
    "1": {
        "timestamp": 1728318841,
        "ifHcOctetsin": 762889,
        "ifHcOctetsOut": 424413
        .... Autres données disponibles.....
    }
```
Ci-dessus, nous pouvons observer un exemple de données sauvegardés. En fonction de nos besoins il sera assez facile des OIDS.

#### Logs?

## Fonctionnement de l'application
L'application pourra se découper en 4 grandes parties.
* Le site WEB
* Le SNMP
* Les fichiers de Configuration
* L'affichage des données 

Nous vous proposons dans un premier temps un schéma résumant notre application:
![Alt text](Projet-Monitoring.jpg)


Au sein du code, nous distinguerons 3 grandes parties.
* SNMP(PYSNMP) se chargera de requêter les oids configurés pour chacune des machines. Ces Oids sont configurés sous forme de tableau JSON. Chaque machine peut avoir des oids particuliers
* L'api renvoie les données récoltées par la partie SNMMP de notre programme en fonction du numéro de machine requêté.
* Le serveur web fait simplement office de vitrine pour
    * L'affichage des résultats
    * L'ajout et la suppression d'une machine


### Notre avancement au 13/10
Nous sommes capables d'ajouter une machine avec plusieurs OIDS. Les requêtes SNMP sont fonctionnelles, nous sommes capable de stocker durablement les données dans des fichiers json. Chaque fichier JSON est propre à une machine.







