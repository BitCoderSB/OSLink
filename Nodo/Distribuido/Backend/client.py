# client.py
import requests
import json
import os
CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.json'))

def load_nodes():
    if not os.path.exists(CONFIG_FILE):
        print("No se encontró config.json.")
        return {}
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
        nodes = config.get("nodes", {})
        # Agrega el nodo local (este mismo)
        nodes[config["node_id"]] = ["127.0.0.1", config["port"]]
        return nodes


def is_node_alive(host, port):
    try:
        r = requests.get(f"http://{host}:{port}/log", timeout=2)
        return r.status_code == 200
    except:
        return False
def send_file(target_host, port, filename, content=None, replicate_to=None):
    import base64, os
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'shared'))
    full_path = os.path.join(BASE_DIR, filename.replace("/", os.sep))
    url = f"http://{target_host}:{port}/transfer"

    try:
        if content is None:
            if not os.path.exists(full_path):
                print(f"[!] Archivo no encontrado: {full_path}")
                return
            with open(full_path, "rb") as f:
                content_bytes = f.read()
        else:
            content_bytes = content if isinstance(content, bytes) else content.encode('utf-8', errors='ignore')

        # Codificar a base64
        encoded = base64.b64encode(content_bytes).decode("utf-8")
        data = {"filename": filename, "content": encoded, "binary": True}

        # Enviar al nodo destino
        requests.post(url, json=data, timeout=5)
        print(f"[➡] Archivo '{filename}' enviado a {target_host}:{port}")

    except Exception as e:
        print(f"[!] Error enviando a {target_host}:{port}: {e}")
        return

    # Replicar
    if replicate_to:
        for rhost, rport in replicate_to:
            if (rhost, rport) != (target_host, port):
                try:
                    replica_filename = f"__replica__/{filename}"
                    replica_data = {"filename": replica_filename, "content": encoded, "binary": True}
                    requests.post(f"http://{rhost}:{rport}/transfer", json=replica_data, timeout=5)
                    print(f"[🧪] Replica enviada a {rhost}:{rport} como '{replica_filename}'")
                except Exception as e:
                    print(f"[!] Error replicando a {rhost}:{rport}: {e}")
def send_folder(host, port, folder_relpath, replicate_to=None):
    import os, base64
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..', 'shared'))
    folder_path = os.path.join(BASE_DIR, folder_relpath.replace("/", os.sep))

    if not os.path.exists(folder_path):
        print(f"[!] Carpeta no encontrada: {folder_path}")
        return

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, BASE_DIR).replace("\\", "/")
            with open(full_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                data = {"filename": rel_path, "content": encoded, "binary": True}
                try:
                    requests.post(f"http://{host}:{port}/transfer", json=data, timeout=5)
                    print(f"[📁] Archivo '{rel_path}' transferido a {host}:{port}")
                    if replicate_to:
                        for rhost, rport in replicate_to:
                            if (rhost, rport) != (host, port):
                                requests.post(f"http://{rhost}:{rport}/transfer", json=data, timeout=5)
                except Exception as e:
                    print(f"[!] Error al transferir '{rel_path}': {e}")

def delete_file(target_host, port, filename):
    url = f"http://{target_host}:{port}/delete"
    data = {"filename": filename}
    try:
        r = requests.post(url, json=data, timeout=5)
        if r.status_code == 200:
            print(f"[+] Archivo '{filename}' eliminado en {target_host}:{port}")
        else:
            print(f"[!] Error al eliminar archivo: {r.status_code}")
    except Exception as e:
        print(f"[!] Error al eliminar archivo: {e}")
