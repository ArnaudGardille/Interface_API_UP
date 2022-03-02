# Interface de récupération des factures UnifiedPost

## Lancement de l'interface
L'interface repose sur un environnement python. Nous vous recommandons d'installer Anaconda. Depuis le terminal, vous devez effectuer les lignes de commandes suivantes : 
(En remplaçant ... par le chemin du répertoire)

On créer un environnement :

conda create -n UnifiedPost-env python=3.10

conda activate UnifiedPost-env

On installe les dépendances :

cd .../Interface_API

pip install -r requirements.txt

Pour lancer l'interface, il suffira d’executer :

streamlit run interface.py

## Fonctionnement de l'interface
L'interface est basée sur l'api accessible via 
https://jefacture.nomadeskpartner.com/comapi-docs/