from flask import Flask, jsonify, render_template, request, redirect, url_for
import json
import os
from functionObject import *
from functions import *
import os
import sys
import subprocess
from dotenv import load_dotenv


load_dotenv()

confFilePath = str(os.getenv('CONF_FILE_PATH'))
dataFilePath = os.getenv('DATA_FILE_PATH')
correspondance_file_path = os.getenv('CORRESPONDANCE_FILE_PATH')
thread_state = {}

# Initialiser Flask et le gestionnaire de threads SNMP
app = Flask(__name__)
snmp_manager = SNMPManager()
log_manager = LogManager(log_file="./application.log")

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
    oid_list = [snmp_correspondences[name] for name in selected_names if name in snmp_correspondences]
    print(f"Received OIDs: {oid_list}")  # Debugging line

    # Création du fichier JSON du dispositif
    id, path = createJsonFile(hostname, ipAddress, snmp_community, oid_list)
    
    # Ajouter le thread pour ce nouveau dispositif
    log_manager.log_creation(id, hostname, ipAddress)
    
    snmp_manager.start_one_thread(id,ipAddress,snmp_community, oid_list, path)  # Start SNMP collection thread for the new device
    
    
    return redirect(url_for('index'))


@app.route('/test')
def please():
    # Retourne l'état des threads
    return str(snmp_manager.thread_state)


@app.route('/devicesData')
def getDataFromDevices():
    deviceId = request.args.get('id')
    device_file_path = os.path.join(dataFilePath, f"{deviceId}.json")
    
    if os.path.exists(device_file_path):
        with open(device_file_path, 'r') as file:
            jsonData = json.load(file)
        return jsonify(jsonData)
    else:
        return jsonify({"message": "Device data not found"}), 404

@app.route('/devices', methods=['GET'])
def devices():
    id = request.args['id']
    oid_list = recup_oid(str(id))
    name_list = []
    for oid in oid_list :
        name = get_name_from_oid(oid)
        name_list.append(name)
    return render_template('devices.html', name_list=name_list, device_id = id )


@app.route('/edit_devices')
def edit_devices():
    deviceId = request.args.get('id')
    # Logique pour éditer les dispositifs
    return jsonify({"message": "Edit device not yet implemented"})


@app.route('/delete_device')
def delete_devices():
    deviceId = request.args.get('id')

    # Arrêter le thread pour ce dispositif
    print(f"Stopping SNMP thread for device {deviceId}")
    print("Etat des threads avant:", snmp_manager.thread_state)
    
    snmp_manager.stop_device_thread(deviceId)
    
    delete_device_from_conf(deviceId)
    log_manager.log_deletion(deviceId)
    with open(confFilePath, 'r') as f:
        devices_data = json.load(f)
    return render_template('index.html', devices=devices_data)

@app.route('/ping_devices')
def ping_devices():
    with open(confFilePath, 'r') as f:
        devices_data = json.load(f)

    results = {}
    for device_id, device_info in devices_data.items():
        ip = device_info['ipAddress']
        try:
            # Run ping command (adjust for Windows)
            response = subprocess.run(
                ["ping", "-n", "1", "-w", "1000", ip],  # '-w 1000' adds a 1-second timeout
                stdout=subprocess.DEVNULL,  # Discard output
                stderr=subprocess.DEVNULL
            )
            # If the return code is 0, the host is reachable
            status = "reachable" if response.returncode == 0 else "unreachable"
            log_manager.log_ping_status(device_id, status)  # Log ping status
            results[device_id] = {"status": status}
        except Exception as e:
            status = "unreachable"
            log_manager.log_ping_status(device_id, status)  # Log ping status
            results[device_id] = {"status": status}
    return jsonify(results)


@app.route('/')
def index():
    # Charger les données des dispositifs
    with open(confFilePath, 'r') as f:
        devices_data = json.load(f)
    return render_template('index.html', devices=devices_data)

def run_snmp_threads():
    print("Starting SNMP threads")
    snmp_manager.start_all_threads()

if __name__ == '__main__':
    # Create the SNMP manager
    snmp_manager = SNMPManager()

    # Start SNMP threads in a separate thread
    snmp_thread = threading.Thread(target=run_snmp_threads)
    snmp_thread.daemon = True  # Ensures the thread will exit when the main program exits
    snmp_thread.start()

    # Start the Flask app
    app.run(debug=True, host='0.0.0.0')