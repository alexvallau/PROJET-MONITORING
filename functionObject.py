from flask import Flask, jsonify, render_template, request
from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity, getCmd
import threading
import time
import json
import os
import random
import logging
from datetime import datetime



class LogManager:
    def __init__(self, log_file):
        self.log_file = log_file
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )
        logging.info("Log Manager initialized.")

    def log_creation(self, device_id, hostname, ip_address):
        message = f"Device created: ID={device_id}, Hostname={hostname}, IP={ip_address}"
        logging.info(message)
        print(message)  # Optional: Print to console

    def log_deletion(self, device_id):
        message = f"Device deleted: ID={device_id}"
        logging.info(message)
        print(message)  # Optional: Print to console

    def log_ping_status(self, device_id, status):
        message = f"Device ping status: ID={device_id}, Status={status}"
        logging.info(message)
        print(message)  # Optional: Print to console




class DeviceThreadManager:
    def __init__(self, device_id, ip, community_string, oids, data_file_path, snmp_manager):
        self.device_id = device_id
        self.ip = ip
        self.community_string = community_string
        self.oids = oids
        self.data_file_path = data_file_path
        self.stop_event = threading.Event()
        self.snmp_manager = snmp_manager
        self.thread = threading.Thread(target=self.collect_data)

    def start(self):
        print(f"Starting thread for device {self.device_id}")
        with self.snmp_manager.lock:
            self.snmp_manager.thread_state[self.device_id] = "running"
        self.thread.start()

    def stop(self):
        print(f"Stopping thread for device {self.device_id}")
        self.stop_event.set()
        self.thread.join()
        with self.snmp_manager.lock:
            self.snmp_manager.thread_state[self.device_id] = "stopped"

    def collect_data(self):
        try:
            with open(self.data_file_path, 'r') as file:
                data = json.load(file)
                entry_id = len(data) + 1 if isinstance(data, dict) else 1
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}
            entry_id = 1

        current_data = {"timestamp": int(time.time())}
        for oid in self.oids:
            if self.stop_event.is_set():
                break
            snmp_name = get_name_from_oid(oid)
            error_indication, error_status, error_index, var_binds = next(
                getCmd(SnmpEngine(),
                        CommunityData(self.community_string),
                        UdpTransportTarget((self.ip, 161), timeout=1, retries=1),
                        ContextData(),
                        ObjectType(ObjectIdentity(oid)))
            )
            if error_indication or error_status:
                print(f"Error for {self.ip}: {error_indication or error_status.prettyPrint()}")
                break
            else:
                for var_bind in var_binds:
                    current_value = int(var_bind[1])
                    current_data[f"{snmp_name}"] = current_value
        if not self.stop_event.is_set():
            data[entry_id] = current_data
            entry_id += 1
            save_data1(data, self.data_file_path)
        time.sleep(5)




def delete_device_from_conf(device_id):
    with open(confFilePath, 'r') as fp:
        devices = json.load(fp)
    if device_id in devices:
        del devices[device_id]
        with open(confFilePath, 'w') as fp:
            json.dump(devices, fp, indent=4)
        return True
    return False


def save_data1(data, file_path):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)



def get_name_from_oid(oid):
    with open('snmp_correspondances.json', 'r') as file:
        myJson = json.load(file)
        for name, value in myJson.items():
            if value == oid:
                return name
        return None

#New thread stop dic
delete_new_thread = {}

class SNMPManager:
    def __init__(self):
        self.threads = {}
        self.thread_state = {}
        self.lock = threading.RLock()
        self.stopped_devices = {}

    def start_all_threads(self):
        with open(confFilePath, 'r') as fp:
            devices = json.load(fp)

        while True:
            for device_id, device_info in devices.items():
                if device_id in self.stopped_devices:
                    continue
                # Check if a thread already exists for this device
                #if device_id in self.threads :
                 #   print(f"Thread for device {device_id} is already running. Skipping.")
                    continue

                print(f"Starting thread for device {device_id}")
                manager = DeviceThreadManager(
                    device_id,
                    device_info['ipAddress'],
                    device_info['communityString'],
                    device_info['OID'],
                    device_info["datafFilePath"],
                    self
                )
                self.threads[device_id] = manager
                self.thread_state[device_id] = "running"
                manager.start()
            time.sleep(5)

            

    def start_one_thread(self, device_id, ip, community_string, oids, data_file_path):
        if device_id in self.threads and self.thread_state.get(device_id) == "running":
            print(f"Thread for device {device_id} is already running. Skipping.")
            return

        print(f"Starting single thread for device {device_id}")
        manager = DeviceThreadManager(
            device_id,
            ip,
            community_string,
            oids,
            data_file_path,
            self
        )
        self.threads[device_id] = manager
        self.thread_state[device_id] = "running"
        manager.start()



    def start_one_thread(self, device_id, ip, community_string, oids, data_file_path):
        # Ensure a thread doesn't already exist for this device
        if device_id in self.threads:
            print(f"Thread for device {device_id} is already running.")
            return

        # Create and start a thread for the SNMP loop
        thread = threading.Thread(target=device_snmp_loop, args=(device_id, ip, community_string, oids, data_file_path, self))
        thread.daemon = True  # Ensure it exits with the main program
        thread.start()
        
        print(f"Thread for device {device_id} started.")

    def stop_device_thread(self, device_id):
        #ajoute l'id de device dans la liste des devices stoppés
        self.stopped_devices[device_id] = True
        delete_new_thread[device_id] = True
        if device_id in self.threads:
            del self.threads[device_id]




def device_snmp_loop(device_id, ip, community_string, oids, data_file_path, snmp_manager):
    while device_id not in snmp_manager.stopped_devices or device_id not in delete_new_thread:
        print(f"Starting SNMP collection for device {device_id}")
        manager = DeviceThreadManager(
            device_id,
            ip,
            community_string,
            oids,
            data_file_path,
            snmp_manager
        )
        snmp_manager.threads[device_id] = manager
        snmp_manager.thread_state[device_id] = "running"
        manager.collect_data()  # Perform one cycle of SNMP data collection
       


confFilePath = r'C:\\Users\\Arizzi Alexandre\\Documents\\Apprentissage\\TRI\\Master 2\\Projet Developpement\\devicesConfiguration\\devicesConf.json'
