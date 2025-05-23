#Sincronización de nodos caídos
import requests, json, os

def sync_from_peer(peer_host, peer_port):
    url = f"http://{peer_host}:{peer_port}/log"
    try:
        response = requests.get(url)
        ops = response.json()
        for op in ops:
            path = f"shared/{op['filename']}"
            if op["action"] == "transfer" and not os.path.exists(path):
                print(f"Falta {path}, retransferirlo manualmente o implementar fetch")
            elif op["action"] == "delete" and os.path.exists(path):
                os.remove(path)
    except Exception as e:
        print(f"No se pudo sincronizar desde {peer_host}:{peer_port} => {e}")
