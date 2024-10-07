from flask import Flask, jsonify, render_template, request
from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, nextCmd, getCmd
import threading
import time
import json
import os
import random
import string


app = Flask(__name__)
data_file = 'data.json'
#data = [] 
snmp_target = '192.168.141.97'  # Replace with the target IP address
snmp_community = 'public'  # Replace with the SNMP community string
snmp_oid = '1.3.6.1.2.1.2.2.1.10.2'  # OID for ifOutOctets for the first interface

confFilePath = r'C:\\Users\\Arizzi Alexandre\\Documents\\Apprentissage\\TRI\\Master 2\\Projet Developpement\\devicesConfiguration\\devicesConf.json'
dataFilePath = r'C:\\Users\\Arizzi Alexandre\\Documents\\Apprentissage\\TRI\\Master 2\\Projet Developpement\\devicesJsonData'


def returnRandom():
    return random.randint(1,100000000)

def getDevicesIdFromJsonConfFile():

    myjson={}
    keys=[]

    with open(confFilePath,'r') as fr:
        myjson = json.load(fr)

    for device_id in myjson.keys():
        print("Keys are "+device_id)
        keys.append(device_id)

    return keys

def createJsonFile(hostname, ipAddress, communityString, OID_list):
    random_value = returnRandom()
    str_random = str(random_value)
    
    # Modèle JSON pour le nouvel appareil
    jsonModel = {
        str_random: {
            "hostname": hostname,
            "ipAddress": ipAddress,
            "communityString": communityString,
            "OID": OID_list,  # Assure-toi que OID_list est une liste
            "datafFilePath": f"{dataFilePath}\\\\{str_random}.json"
        }
    }
    fileName = f"{str_random}.json"
    
    # Créer un nouveau fichier de données pour l'appareil
    with open(os.path.join(dataFilePath, fileName), 'w') as json_file2:
        json.dump([], json_file2)  # Crée un fichier JSON vide pour les données
    
    # Assure-toi que le fichier de configuration existe
    if not os.path.isfile(confFilePath):
        with open(confFilePath, 'w') as json_file3:
            json.dump({}, json_file3)  # Initialise en tant que dictionnaire vide
    
    # Charger le fichier de configuration et s'assurer que c'est un dictionnaire
    with open(confFilePath, 'r') as fp:
        try:
            myJson = json.load(fp)
            if not isinstance(myJson, dict):
                myJson = {}  # Si le contenu n'est pas un dictionnaire, faire un dictionnaire vide
        except json.JSONDecodeError:
            myJson = {}  # En cas d'erreur de parsing, initialise comme dictionnaire vide
    
    # Ajouter le nouvel appareil au JSON
    myJson.update(jsonModel)
    
    # Sauvegarder le fichier de configuration mis à jour
    with open(confFilePath, 'w') as json_file:
        json.dump(myJson, json_file, indent=4)

    print(f"Device added successfully with ID {random_value}")

    

def load_data():
    global data
    if os.path.exists(data_file):
        with open(data_file, 'r') as file:
            data = json.load(file)

""" def save_data():
    with open(data_file, 'w') as file:
        json.dump(data, file) """

def save_data1(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file)

def load_snmp_correspondences():
    with open('snmp_correspondances.json', 'r') as file:
        return json.load(file)





def collect_data_for_device(device_ip, community_string, oid, data_file_path):
    previous_value = None

    data = []  # Device-specific data list
    while True:
        error_indication, error_status, error_index, var_binds = next(
            getCmd(SnmpEngine(),
                   CommunityData(community_string),
                   UdpTransportTarget((device_ip, 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity(oid)))
        )

        if error_indication:
            print(f"Error for {device_ip}: {error_indication}")
        elif error_status:
            print(f"Error for {device_ip}: {error_status.prettyPrint()}")
        else:
            for var_bind in var_binds:
                current_value = int(var_bind[1])
                if previous_value is not None:
                    print(f"Data from {device_ip}: {current_value}")
                    data.append(current_value)  # Append current value to device-specific data list
                    
                    # Save the data to the appropriate file
                    save_data1(data, data_file_path)  # Save updated data to the JSON file

                    # Optional: Control data length (keep only the last 30 days)
                    if len(data) > 2592000:  # Keep only the last 30 days (1 minute of data if collected every second)
                        data.pop(0)

                previous_value = current_value
        time.sleep(5)


def start_snmp_threads():
    with open(confFilePath, 'r') as fp:
        devices = json.load(fp)
    
    for device_id, device_info in devices.items():
        device_ip = device_info['ipAddress']
        community_string = device_info['communityString']
        oid = device_info['OID']
        dataFilePath = device_info["datafFilePath"]
        
        # Start a thread for each device
        threading.Thread(target=collect_data_for_device, args=(device_ip, community_string, oid, dataFilePath), daemon=True).start()


""" @app.route('/data')
def get_data():
    return jsonify(data) """



@app.route('/test')
def please():
    return getDevicesIdFromJsonConfFile()

@app.route('/add')
def create_Device():
    return render_template('addDevice.html')



""" @app.route('/submitDevice', methods=['POST'])
def submit_Device():
    hostname = request.form['hostname']
    ipAddress = request.form['ipAddress']
    snmp_community = request.form['community']
    
    # Capture the list of OIDs
    oid_list = request.form.getlist('oid[]')  # Ensure this matches the input name
    print(f"Received OIDs: {oid_list}")  # Debugging line
    
    # Format the OIDs into a single dictionary
    snmp_oids = {}
    for oid in oid_list:
        if ':' in oid and len(oid.split(":")) == 2:
            key, value = oid.split(":")
            snmp_oids[key.strip()] = value.strip()  # Use key as dictionary key

    print(f"Formatted OIDs: {snmp_oids}")  # Debugging line

    # Call your JSON file creation function
    createJsonFile(hostname, ipAddress, snmp_community, snmp_oids)
    
    return jsonify({"message": "Device added successfully"}) """


@app.route('/submitDevice', methods=['POST'])
def submit_Device():
    hostname = request.form['hostname']
    ipAddress = request.form['ipAddress']
    snmp_community = request.form['community']
    
    # Récupérer la liste des noms sélectionnés
    selected_names = request.form.getlist('oid[]')
    
    # Charger les correspondances SNMP
    snmp_correspondences = load_snmp_correspondences()

    # Trouver les OIDs correspondant aux noms sélectionnés
    oid_list = []
    for name in selected_names:
        if name in snmp_correspondences:
            oid_list.append(snmp_correspondences[name])

    print(f"Received OIDs: {oid_list}")  # Ligne de débogage

    # Appel de ta fonction de création de fichier JSON
    createJsonFile(hostname, ipAddress, snmp_community, oid_list)
    
    return jsonify({"message": "Device added successfully"})


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    #load_data()
    #threading.Thread(target=collect_data, daemon=True).start()
    start_snmp_threads()
    app.run(debug=True)