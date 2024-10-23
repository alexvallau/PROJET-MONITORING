from flask import Flask, jsonify, render_template, request
from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, nextCmd, getCmd
import threading
import time
import json
import os
import random
import string
from functions import *


app = Flask(__name__)




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



@app.route('/test')
def please():
    oid_list = recup_oid(str(92202993))
    name_list = []
    for oid in oid_list :
        name = get_name_from_oid(oid)
        name_list.append(name)
    return name_list

#API qui renvoi les données
@app.route('/devicesData')
def getDataFromDevices():
    deviceId = request.args.get('id')
    with open(os.path.join(dataFilePath,str(deviceId)+'.json'),'r') as file:
        jsonData = json.load(file)
    return jsonData

## A
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