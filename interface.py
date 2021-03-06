from functools import cache
import streamlit as st
import requests
import json
import os.path
import os
from pathlib import Path
import sys
sys.tracebacklimit = 0


@st.cache #met le réslutat de la fonction en mémoire pour des arguments donnés
def get_clients(headers, url):
    """ 
    Cette fonction récupère la liste des clients d'un cabinet.

    Renvoit une liste de dictionnaires de type:
    {
    "name": "Manet FR61453416687",
    "siren": "453416687"
    }
    """
    request_url = url + '/enterprise'
    r = requests.get(request_url, headers=headers) # On effectue la requète

    r.raise_for_status() # Si l'api a rencontré une erreur, on l'affiche à l'utilisateur

    content = json.loads(r.content) # On convertit la réponse de la requète au format json 
    return content

# On ne sauvegarde pas la réponse de la fonction, car les fichiers sont suceptibles de 
# changer de répertoire en raison des téléchargements.
def get_files(client, invoice_type, headers, url):
    """
    Cette fonction récupère la liste des noms de fichier pour un client donné.
    Les fichiers peuvent être dans 'Transfer' ou 'Archived'

    client: le SIREN
    invoice_type: AP ou AR
     
    renvoit une liste de dictionnaires du type:
    {
    "name": "udr_20210425_CA94104_5401_a908a08f4b6144bfa7f369695a20b841.pdf",
    "size": 145985,
    "mtime": 1640274195,
    "ctime": 1645095452,
    "downloadurl": "https://jefacture.nomadeskpartner.com/comapi/invoice/download/477598601/AP/Archived/udr_20210425_CA94104_5401_a908a08f4b6144bfa7f369695a20b841.pdf"
    }
    """
    content = []
    for status in ['Transfer', 'Archived']: 
        request_url = url + "/invoice/" + client + "/" + invoice_type + "/" + status

        r = requests.get(request_url, headers=headers) # On effectue la requète

        assert r.status_code == 200
        content += json.loads(r.content) # On convertit la réponse de la requète au format json 
    return content

@st.cache # On sauvegarde le résultat pour ne par télécharger plusieurs fois un même fichier 
def download_file(url, headers):
    """
    Cette fonction télécharge un fichier pdf en le conidérant comme un fichier binaire.
    """
    return requests.get(url, headers=headers) # On effectue la requète

def save_file(binary_pdf, path):
    """
    Si le fichier n'existe pas déjà, cette fonction l'enregiste dans le chemin indiqué.
    """
    if os.path.exists(path):
        print("Le fichier existe déjà")
    else:
        saved_file = open(path, "wb")
        saved_file.write(binary_pdf.content)
        saved_file.close()


environnement = st.sidebar.radio("Environnement", ['UAT', 'PROD']) # On choisit entre UAT et PROD

# On met a jour l'url en conséquent
if environnement == 'UAT':
    url = "https://jefacture.nomadeskpartner.com/comapi/v1"
else:
    url = "https://fichiers.jefacture.com/comapi/v1"

# On demande les clefs d'identification
ApiKeyAuth = st.sidebar.text_input("ApiKeyAuth", value="") 
SoftwareID = st.sidebar.text_input("SoftwareID", value="")

# On let met dans un 'header', afin de les envoyer dans nos requètes
headers= { 'X-SOFTWARE-ID': SoftwareID, 'X-API-KEY' : ApiKeyAuth}

clients = get_clients(headers, url) #On récupère les clients du cabinet

siren_list = [] # Liste des sirens
name_dict = {} # Disctionnaire qui associe un nom a son siren respectif
for client in clients:
    name = client['name']
    siren = client['siren']

    siren_list.append(siren)
    name_dict[siren] = name

name_col, siren_col = st.columns(2)

if 'index' not in globals(): #si la variable n'existe pas..
    index = 0

if 'index' not in st.session_state: # idem, mais pour les variables internes de Streamlit
	st.session_state.index = 0

sirens = st.multiselect("Sirens", siren_list, key="sirens") # On peut choisit des siens parmi la liste

siren_col, descr_col, ap_col, ar_col = st.columns([2, 5, 1, 1]) # On fait des colonnes de différentes tailles, pour que ca soit jolie

# Le dictionnaire 'siren_ap_ar_dict' associe une liste de deux booléens à chaque siren séléctionné.
# Le premier est vrai si on a coché AP, le second si on a coché AR

if 'siren_ap_ar_dict' not in globals(): # si la variable n'existe pas..
    siren_ap_ar_dict = {}

# Les titres du tableau
with siren_col:
    st.subheader("Siren")

with descr_col:
    st.subheader("Description")

with ap_col:
    st.subheader("AP")

with ar_col:
    st.subheader("AR")

# On trie les sirens
sirens = sorted(sirens)

for siren in sirens:
    if siren not in siren_ap_ar_dict.keys():
        siren_ap_ar_dict[siren] = [True, True] # AP et AR sont cochés par defaut

    with siren_col:
        st.text(siren)

    with descr_col:
        st.text(name_dict[siren])

    with ap_col:
        siren_ap_ar_dict[siren][0] = st.checkbox("", value=siren_ap_ar_dict[siren][0], key="ap_"+str(siren))
        # Si la case est cochée, on change la valeur du dictionnaire

    with ar_col:
        siren_ap_ar_dict[siren][1] = st.checkbox("", value=siren_ap_ar_dict[siren][1], key="ar_"+str(siren))
        # Si la case est cochée, on change la valeur du dictionnaire

default_path = Path(__file__).parent.resolve() # le chemin par defaut de sauvegarde des factures sela celui ou se trouve ce programme
path_str = st.text_input("Chemin du dossier de synchronisation", value=default_path) # Il est néamoins possible de le changer

if st.button("Lancer la requète", disabled=sirens==[]):
    # On ajoute une bar de progression
    my_bar = st.progress(0.0)
    frac_progress = 1.0 / len(sirens)
    percent_complete = 0.0

    for siren in sirens:

        if siren_ap_ar_dict[siren][0]: # AP est coché
            files_json = get_files(siren, 'AP', headers, url) # On récupère la liste des fichiers

            path = Path(path_str) / siren / 'AP'
            os.makedirs(path, exist_ok=True)

            for file in files_json:
                file_path = path / file['name']

                if not os.path.exists(file_path): # Si le fichier n'existe pas déjà
                    pdf = download_file(file['downloadurl'], headers) # On télécharge
    
                    save_file(pdf, file_path) # On sauvegarde


        if siren_ap_ar_dict[siren][1]: # AR est coché
            files_json = get_files(siren, 'AR', headers, url) # On récupère la liste des fichiers
            
            for file in files_json:
                pdf = download_file(file['downloadurl'], headers)
                path = Path(path_str) / siren / 'AR'
                os.makedirs(path, exist_ok=True)

                save_file(pdf, path / file['name'])

        percent_complete += frac_progress
        my_bar.progress(min(percent_complete, 1.0))
        
    my_bar.progress(1.0)



            


