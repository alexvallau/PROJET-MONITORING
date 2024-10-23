from flask import Flask, jsonify, render_template, request
from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, nextCmd, getCmd
import threading
import time
import json
import os
import random
import string

confFilePath = r'C:\\Users\\Arizzi Alexandre\\Documents\\Apprentissage\\TRI\\Master 2\\Projet Developpement\\devicesConfiguration\\devicesConf.json'
dataFilePath = r'C:\\Users\\Arizzi Alexandre\\Documents\\Apprentissage\\TRI\\Master 2\\Projet Developpement\\devicesJsonData'
correspondanceFilePath = r'C:\\Users\\Arizzi Alexandre\\Documents\\Apprentissage\\TRI\\Master 2\\Projet Developpement\\snmp_correspondances.json'

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
    threading.Thread(target=collect_data_for_device, args=(ipAddress, communityString, OID_list, f"{dataFilePath}\\\\{str_random}.json"), daemon=True).start()

    
def recup_oid(id):
    with open(confFilePath, 'r') as fp:
        devices = json.load(fp)
        if id in devices : 
            return devices[id]["OID"]
        else : 
            return 0


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
    
    print(f"Collecting data for{device_ip} with community string {community_string} and OIDs {oids}")
    ##Check if data file exist
    try:
        with open(data_file_path, 'r') as file:
            data = json.load(file)
            if not isinstance(data, dict):
                data = {}
            entry_id = len(data) + 1
    except (json.JSONDecodeError, FileNotFoundError):
        data = {}
        entry_id = 1

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
        print(entry_id)
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
