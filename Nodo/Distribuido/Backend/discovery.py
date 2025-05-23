import socket
import threading
import json
import time
import os
import requests
from datetime import datetime

PORT = 6000

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")
SHARED_DIR = os.path.join(ROOT_DIR, "shared")


def broadcast_hello(my_id, my_port):
    msg = json.dumps({"node_id": my_id, "port": my_port})
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        try:
            sock.sendto(msg.encode(), ('192.168.131.255', PORT))
        except Exception as e:
            print(f"[!] Error enviando broadcast: {e}")
        time.sleep(5)


def listen_for_nodes(my_id, my_port):
    peers = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    try:
        sock.bind(('', PORT))
    except OSError as e:
        print(f"[!] Error en bind UDP: {e}")
        return

    start_time = time.time()
    while time.time() - start_time < 15:
        try:
            data, addr = sock.recvfrom(1024)
            info = json.loads(data.decode())
            ip = addr[0]
            print(f"📡 Recibido de {ip}: {info}")
            if info['node_id'] != my_id:
                peers[info['node_id']] = [ip, info['port']]
                print(f"🔍 Nodo detectado: {info['node_id']} @ {ip}:{info['port']}")

        except socket.timeout:
            continue
        except Exception as e:
            print(f"[!] Error decoding UDP: {e}")

    # Siempre incluye el nodo actual
    peers[my_id] = ["127.0.0.1", my_port]
    save_config(my_id, my_port, peers)


def save_config(my_id, my_port, new_nodes):
    # Cargar configuración existente
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            existing_nodes = config.get("nodes", {})
    except:
        existing_nodes = {}

    # Fusionar nodos
    updated_nodes = existing_nodes.copy()
    updated_nodes.update(new_nodes)  # sobreescribe si hay nodos duplicados

    config_data = {
        "node_id": my_id,
        "port": my_port,
        "nodes": {k: v for k, v in updated_nodes.items() if k != my_id}
    }

    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=2)
        print("💾 Config actualizada (fusionada):", config_data)
    except Exception as e:
        print(f"[!] Error guardando config.json: {e}")

def sincronizar_archivos(my_id, my_port):
    # Cargar log local
    try:
        with open(os.path.join(ROOT_DIR, "log.json"), "r") as f:
            mi_log = json.load(f)
    except:
        mi_log = []

    # Cargar nodos conocidos
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            nodes = config.get("nodes", {})
    except:
        nodes = {}

    for nodo_id, (host, port) in nodes.items():
        try:
            r = requests.get(f"http://{host}:{port}/log", timeout=3)
            if r.status_code != 200:
                continue
            log_otro = r.json()

            mis_acciones = {(op['action'], op['filename']) for op in mi_log}
            acciones_faltantes = [op for op in log_otro if (op['action'], op['filename']) not in mis_acciones]
            from client import send_file,delete_file
            for op in acciones_faltantes:
                archivo = op['filename']
                if op['action'] == "transfer":
                    print(f"🔄 Sincronizando '{archivo}' desde {nodo_id}")
                    content = requests.get(f"http://{host}:{port}/shared/{archivo}", timeout=3).content.decode()
                    dest_host, dest_port = nodes[nodo_id]
                    send_file(dest_host, dest_port, archivo, content)
                elif op['action'] == "delete":
                    print(f"🗑 Eliminando '{archivo}' en nodo reconectado")
                    dest_host, dest_port = nodes[nodo_id]
                    delete_file(dest_host, dest_port, archivo)
        except Exception as e:
            print(f"[!] Error al sincronizar con {nodo_id}: {e}")


def periodic_listen(my_id, my_port):
    while True:
        listen_for_nodes(my_id, my_port)
        time.sleep(60)


def start_discovery(my_id, my_port):
    from client import send_file, delete_file

    threading.Thread(target=broadcast_hello, args=(my_id, my_port), daemon=True).start()
    
    # Primera escucha y configuración
    listen_for_nodes(my_id, my_port)
    
    # Sincronización inmediata tras primera escucha
    sincronizar_archivos(my_id, my_port)

    # Lanzar descubrimiento periódico
    threading.Thread(target=periodic_listen, args=(my_id, my_port), daemon=True).start()
