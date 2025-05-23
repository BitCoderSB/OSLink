import requests
import json
from client import load_nodes, send_file, delete_file

def sincronizar_archivos(my_id, my_port):
    # Paso 1: Cargar log local
    try:
        with open("log.json", "r") as f:
            mi_log = json.load(f)
    except:
        mi_log = []

    nodes = load_nodes()
    for nodo_id, (host, port) in nodes.items():
        try:
            # Paso 2: Obtener log de otro nodo
            r = requests.get(f"http://{host}:{port}/log", timeout=3)
            if r.status_code != 200:
                continue
            log_otro = r.json()

            # Paso 3: Detectar operaciones que yo no tengo
            mis_acciones = {(op['action'], op['filename']) for op in mi_log}
            acciones_faltantes = [op for op in log_otro if (op['action'], op['filename']) not in mis_acciones]

            # Paso 4: Aplicar operaciones faltantes
            for op in acciones_faltantes:
                archivo = op['filename']
                if op['action'] == "transfer":
                    print(f"🔄 Descargando '{archivo}' desde {nodo_id}")
                    contenido = requests.get(f"http://{host}:{port}/shared/{archivo}").content.decode()
                    dest_host, dest_port = nodes[nodo_id]
                    send_file(dest_host, dest_port, archivo, contenido)
                elif op['action'] == "delete":
                    print(f"🗑 Eliminando '{archivo}' en nodo reconectado")
                    dest_host, dest_port = nodes[nodo_id]
                    delete_file(dest_host, dest_port, archivo)

        except Exception as e:
            print(f"[!] Error al sincronizar con {nodo_id}: {e}")
