import json
import os
import time
from datetime import datetime
from flask import Flask, request
from flask import jsonify
from discovery import start_discovery

my_id = "nodo4"
my_port = "5004"

start_discovery(my_id, my_port)

app = Flask(__name__)
BASE_DIR = "../../shared"

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

# === Solicita ID y puerto del nodo

# === Inicia descubrimiento


# === Espera a que config.json esté listo y válido
config = {}
for _ in range(10):
    try:
        if os.path.exists(CONFIG_FILE) and os.path.getsize(CONFIG_FILE) > 0:
            with open(CONFIG_FILE, "r") as f:
                raw = f.read()
                print("📄 Raw config.json:", raw)
                config = json.loads(raw)
            break
    except json.JSONDecodeError as e:
        print("❌ JSON mal formado:", e)
    time.sleep(1)
else:
    print("❌ No se pudo generar config.json correctamente.")
    exit(1)

print(f"✅ Nodo {my_id} listo en puerto {config['port']}")
print("🚀 Iniciando servidor...\n")

# === RUTAS DEL SERVIDOR ===
@app.route("/transfer", methods=["POST"])
def transfer():
    data = request.get_json()
    filename = data["filename"]
    content = data["content"]
    is_binary = data.get("binary", False)

    path = os.path.join(BASE_DIR, filename.replace("/", os.sep))
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "wb") as f:
        if is_binary:
            import base64
            f.write(base64.b64decode(content))
        else:
            f.write(content.encode())

    log_operation("transfer", filename)
    return jsonify({"status": "OK"})


@app.route("/delete", methods=["POST"])
def delete():
    data = request.get_json()
    filename = data['filename']
    path = os.path.join(BASE_DIR, filename)

    import shutil

    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        log_operation("delete", filename)
        return jsonify({"status": "deleted"})
    else:
        return jsonify({"status": "not found"}), 404

@app.route("/log", methods=["GET"])
def get_log():
    try:
        with open("log.json", "r") as f:
            return jsonify(json.load(f))
    except:
        return jsonify([])


def log_operation(action, filename):
    if not os.path.exists("log.json"):
        with open("log.json", "w") as f:
            json.dump([], f)

    try:
        with open("log.json", "r") as f:
            log = json.load(f)
    except json.JSONDecodeError:
        log = []

    log.append({"action": action, "filename": filename})
    with open("log.json", "w") as f:
        json.dump(log, f)

from flask import send_from_directory
from flask import send_from_directory
from werkzeug.utils import safe_join

@app.route("/shared/<path:filename>", methods=["GET"])
def get_file(filename):
    try:
        # Evita salir de la carpeta shared con rutas inseguras
        safe_path = safe_join(BASE_DIR, filename)
        dir_name = os.path.dirname(safe_path)
        file_name = os.path.basename(safe_path)
        return send_from_directory(directory=dir_name, path=file_name)
    except Exception as e:
        return jsonify({"error": str(e)}), 404


@app.route("/list_files", methods=["GET"])
def list_files():
    folder = "../../shared"
    try:
        archivos = []
        for filename in os.listdir(folder):
            path = os.path.join(folder, filename)
            if os.path.isfile(path):
                size = os.path.getsize(path)
                modified = os.path.getmtime(path)
                archivos.append({
                    "filename": filename,
                    "size": f"{round(size / 1024, 2)} KB",
                    "modified": datetime.fromtimestamp(modified).strftime("%Y-%m-%d %H:%M:%S")
                })
        return jsonify(archivos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/list_tree", methods=["GET"])
def list_tree():
    def build_tree(path):
        items = []
        for name in os.listdir(path):
            if name.startswith("__replica__"):
                continue  # oculta respaldos
            full = os.path.join(path, name)
            if os.path.isdir(full):
                items.append({
                    "name": name,
                    "children": build_tree(full),
                    "modified": datetime.fromtimestamp(os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M:%S")
                })
            else:
                items.append({
                    "name": name,
                    "size": f"{round(os.path.getsize(full)/1024, 2)} KB",
                    "modified": datetime.fromtimestamp(os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M:%S")
                })
        return items

    try:
        return jsonify(build_tree(BASE_DIR))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Ejecuta servidor
if __name__ == "__main__":
    print(config["port"])
    app.run(host="0.0.0.0", port=config["port"])
