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

confFilePath = r'C:\\Users\\yacin\\OneDrive\\Bureau\\Enseignements\\M2\\PROJET-MONITORING\\devicesConfiguration\\devicesConf.json'
dataFilePath = r'C:\\Users\\yacin\\OneDrive\\Bureau\\Enseignements\\M2\\PROJET-MONITORING\\devicesJsonData\\'
correspondanceFilePath = r'C:\\Users\\yacin\\OneDrive\\Bureau\\Enseignements\\M2\\PROJET-MONITORING\\snmp_correspondances.json'

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



def save_data1(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def load_snmp_correspondences():
    with open('snmp_correspondances.json', 'r') as file:
        return json.load(file)

#retourne 
def get_name_from_oid(oid):
    with open('snmp_correspondances.json','r') as file:
        myJson=json.load(file)
        for name, value in myJson.items():
            if value == oid:
                return name
        return None



def collect_data_for_device(device_ip, community_string, oids, data_file_path):
    
    ##Check if data file exist
    if  os.path.isfile(data_file_path):
        with open(data_file_path, 'r') as file:
            data = json.load(file)
            entry_id = len(data) + 1
    else:
        data = {}
        entry_id = 1
    
      # Dictionary to store data with timestamps
      # Counter for entries



    while True:
        current_data = {"timestamp": int(time.time())}  # Get the current timestamp

        for oid in oids:
            snmp_name = get_name_from_oid(oid)
            error_indication, error_status, error_index, var_binds = next(
                getCmd(SnmpEngine(),
                       CommunityData(community_string),
                       UdpTransportTarget((device_ip, 161)),
                       ContextData(),
                       ObjectType(ObjectIdentity(oid)))
            )

            if error_indication:
                print(f"Error for {device_ip}: {error_indication}")
                break
            elif error_status:
                print(f"Error for {device_ip}: {error_status.prettyPrint()}")
                break
            else:
                for var_bind in var_binds:
                    current_value = int(var_bind[1])
                    current_data[f"{snmp_name}"] = current_value  # Store current value using SNMP name

        # Add the current data to the dictionary with an incremental ID
        data[entry_id] = current_data
        entry_id += 1
        
        # Save the data to the file
        save_data1(data, data_file_path)

        time.sleep(5)  # Wait for 5 seconds before the next collection




def start_snmp_threads():
    with open(confFilePath, 'r') as fp:
        devices = json.load(fp)
    
    for device_id, device_info in devices.items():
        device_ip = device_info['ipAddress']
        community_string = device_info['communityString']
        oids = device_info['OID']  # Assurez-vous que c'est une liste
        dataFilePath = device_info["datafFilePath"]
        
        # Démarrer un thread pour chaque appareil
        threading.Thread(target=collect_data_for_device, args=(device_ip, community_string, oids, dataFilePath), daemon=True).start()



@app.route('/test')
def please():
    return getDevicesIdFromJsonConfFile()

@app.route('/add')
def create_Device():
    return render_template('addDevice.html')





@app.route('/submitDevice', methods=['POST'])
def submit_Device():
    hostname = request.form['hostname']
    ipAddress = request.form['ipAddress']
    snmp_community = request.form['community']
    
    # Récupérer la liste des noms sélectionnés
    selected_names = request.form.getlist('oid[]')
    print(f"Selected OIDs: {selected_names}")  # Debugging line

    # Charger les correspondances SNMP
    snmp_correspondences = load_snmp_correspondences()
    print("SNMP Correspondences:", snmp_correspondences)  # Debugging line

    # Trouver les OIDs correspondant aux noms sélectionnés
    oid_list = []
    for name in selected_names:
        if name in snmp_correspondences:
            oid_list.append(snmp_correspondences[name])
        else:
            print(f"Warning: '{name}' not found in SNMP correspondences.")  # Debugging line

    print(f"Received OIDs: {oid_list}")  # Debugging line

    # Appel de ta fonction de création de fichier JSON
    createJsonFile(hostname, ipAddress, snmp_community, oid_list)
    
    return jsonify({"message": "Device added successfully"})


@app.route('/salut')
def returnData():
    return render_template('data.html')

#API qui renvoi les données
@app.route('/devicesData')
def getDataFromDevices():
    deviceId = request.args.get('id')
    with open(os.path.join(dataFilePath,str(deviceId)+'.json'),'r') as file:
        jsonData = json.load(file)
    return jsonData


@app.route('/devices')
def devices():
    # Load the devices data
    with open(confFilePath, 'r') as f:
        devices_data = json.load(f)
    # Pass the updated devices data to the HTML template
    return render_template('devices.html', devices=devices_data)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':

    start_snmp_threads()
    app.run(debug=True)