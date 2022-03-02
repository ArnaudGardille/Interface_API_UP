from functools import cache
import streamlit as st
import requests
import json
import os.path
import os
from pathlib import Path
import sys
sys.tracebacklimit = 0


@st.cache
def get_clients(headers, url):
    """ 
    Renvoit une liste de dictionnaires de type:
    {
    "name": "Manet FR61453416687",
    "siren": "453416687"
    }
    """
    r = requests.get(url, headers=headers)

    r.raise_for_status()
    
    print("content: ", r.content)
    print("headers: ", r.headers)
    print("reason: ", r.reason)
    print("text: ", r.text)
    content = json.loads(r.content)
    return content

#@st.cache
def get_files(client, invoice_type, headers, url):
    """
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
        request_url = url + "/v1/invoice/" + client + "/" + invoice_type + "/" + status
        #print('url: ', url)
        r = requests.get(request_url, headers=headers)
        #print(r.status_code)
        assert r.status_code == 200
        content += json.loads(r.content)
        #print(len(content))
        
    return content

@st.cache
def download_file(url, headers):
    return requests.get(url, headers=headers)

def save_file(binary_pdf, path):
    #print("type: ", type(binary_pdf))
    if os.path.exists(path):
        print("Le fichier existe déjà")
    else:
        saved_file = open(path, "wb")
        saved_file.write(binary_pdf.content)
        saved_file.close()


environnement = st.sidebar.radio("Environnement", ['UAT', 'PROD'])

if environnement == 'UAT':
    url = "https://jefacture.nomadeskpartner.com/comapi/v1/enterprise"
else:
    url = "https://fichiers.jefacture.com/comapi/"

ApiKeyAuth = st.sidebar.text_input("ApiKeyAuth", value="")
SoftwareID = st.sidebar.text_input("SoftwareID", value="")

headers= { 'X-SOFTWARE-ID': SoftwareID, 'X-API-KEY' : ApiKeyAuth}

clients = get_clients(headers, url)
siren_dict = {}
name_dict = {}
for client in clients:
    name = client['name']
    siren = client['siren']

    siren_dict[name] = siren
    name_dict[siren] = name

name_list = list(name_dict.values())
siren_list = list(siren_dict.values())

name_col, siren_col = st.columns(2)

if 'index' not in globals(): #la variable n'existe pas
    index = 0

if 'index' not in st.session_state:
	st.session_state.index = 0

sirens = st.multiselect("Sirens", siren_list, key="sirens")

siren_col, descr_col, ap_col, ar_col = st.columns([2, 5, 1, 1])

if 'siren_ap_ar_dict' not in globals(): #la variable n'existe pas
    siren_ap_ar_dict = {}

with siren_col:
    st.subheader("Siren")

with descr_col:
    st.subheader("Description")

with ap_col:
    st.subheader("AP")

with ar_col:
    st.subheader("AR")

sirens = sorted(sirens)

for siren in sirens:
    if siren not in siren_ap_ar_dict.keys():
        siren_ap_ar_dict[siren] = [True, True]

    with siren_col:
        st.text(siren)

    with descr_col:
        st.text(name_dict[siren])

    with ap_col:
        siren_ap_ar_dict[siren][0] = st.checkbox("", value=siren_ap_ar_dict[siren][0], key="ap_"+str(siren))

    with ar_col:
        siren_ap_ar_dict[siren][1] = st.checkbox("", value=siren_ap_ar_dict[siren][1], key="ar_"+str(siren))

default_path = Path(__file__).parent.resolve()
path_str = st.text_input("Chemin du dossier de synchronisation", value=default_path)



if st.button("Lancer la requète", disabled=sirens==[]):
    my_bar = st.progress(0.0)
    frac_progress = 1.0 / len(sirens)
    percent_complete = 0.0

    for siren in sirens:
        print(siren_ap_ar_dict[siren])
        if siren_ap_ar_dict[siren][0]:
            files_json = get_files(siren, 'AP', headers, url)

            path = Path(path_str) / siren / 'AP'
            os.makedirs(path, exist_ok=True)

            for file in files_json:
                file_path = path / file['name']

                if not os.path.exists(file_path):
                    pdf = download_file(file['downloadurl'], headers)
    
                    save_file(pdf, file_path)


        if siren_ap_ar_dict[siren][1]:
            files_json = get_files(siren, 'AR', headers, url)
            for file in files_json:
                pdf = download_file(file['downloadurl'], headers)
                path = Path(path_str) / siren / 'AR'
                os.makedirs(path, exist_ok=True)
                save_file(pdf, path / file['name'])

        percent_complete += frac_progress
        my_bar.progress(min(percent_complete, 1.0))
    my_bar.progress(1.0)



            


