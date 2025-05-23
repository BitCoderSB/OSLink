import sys

import requests
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
import random
#from PIL import Image, ImageTk
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Backend')))
from client import send_file, delete_file, load_nodes, is_node_alive


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        try:
            with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.json'))) as f:
                self.local_node = json.load(f).get("node_id", "desconocido")
        except:
            self.local_node = "desconocido"
        self.title("Sistema de Archivos Distribuidos")
        self.geometry("900x700")
        self.resizable(True, True)
        
        # Configuración de estilos con colores vibrantes
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Colores vibrantes
        self.bg_color = "#2c3e50"
        self.accent_color = "#e74c3c"
        self.secondary_color = "#3498db"
        self.success_color = "#2ecc71"
        self.warning_color = "#f39c12"
        
        # Configurar estilos
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TLabel', background=self.bg_color, foreground='white', font=('Helvetica', 10))
        self.style.configure('Title.TLabel', font=('Helvetica', 18, 'bold'), foreground='white')
        self.style.configure('Node.TFrame', borderwidth=3, relief='groove', background='#34495e')
        self.style.configure('NodeHeader.TFrame', background=self.accent_color)
        self.style.configure('NodeHeader.TLabel', font=('Arial', 10, 'bold'), foreground='white', background=self.accent_color)
        self.style.configure('Online.TLabel', foreground=self.success_color, background='#34495e')
        self.style.configure('Offline.TLabel', foreground=self.warning_color, background='#34495e')
        self.style.configure('TButton', background=self.secondary_color, foreground='white')
        self.style.map('TButton', 
                      background=[('active', self.accent_color), ('disabled', '#95a5a6')],
                      foreground=[('active', 'white'), ('disabled', '#7f8c8d')])
        
        # Contenedor principal
        self.container = tk.Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        
        # Diccionario de frames/pantallas
        self.frames = {}
        
        # Crear todas las pantallas
        for F in (StartScreen, LoadingScreen, MainScreen):
            frame = F(self.container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame("StartScreen")
        self.pending_ops = {}  # {"nodo2": [{"action": "transfer", "filename": "x"}, ...]}

    
    def show_frame(self, cont):
        frame = self.frames[cont]
        if cont == "LoadingScreen":
            frame.start_loading()
        frame.tkraise()

class StartScreen(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg=controller.bg_color)
        
        # Logo/Title
        logo_frame = tk.Frame(self, bg=controller.bg_color)
        logo_frame.pack(pady=100)
        
        # Simulación de logo con texto
        ttk.Label(logo_frame, text="DISTRIBUTED FS", style='Title.TLabel').pack()
        ttk.Label(logo_frame, text="Sistema de Archivos Distribuidos", style='TLabel').pack(pady=10)
        
        # Botón de inicio
        start_btn = ttk.Button(
            self, 
            text="Iniciar Sistema", 
            command=lambda: controller.show_frame("LoadingScreen"),
            style='TButton'
        )
        start_btn.pack(pady=50)
        
        # Footer
        ttk.Label(self, text="Versión 1.0 © 2023", style='TLabel').pack(side='bottom', pady=20)

class LoadingScreen(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg=controller.bg_color)
        
        # Configuración de elementos
        ttk.Label(self, text="Inicializando sistema...", style='Title.TLabel').pack(pady=100)
        
        self.progress = ttk.Progressbar(
            self, 
            orient='horizontal', 
            mode='determinate', 
            length=400
        )
        self.progress.pack(pady=20)
        
        self.status_label = ttk.Label(self, text="Conectando con nodos...", style='TLabel')
        self.status_label.pack(pady=10)
    
    def start_loading(self):
        self.progress['value'] = 0
        self.update_progress()
    
    def update_progress(self):
        current_value = self.progress['value']
        if current_value < 100:
            increment = random.randint(5, 15)
            new_value = min(current_value + increment, 100)
            self.progress['value'] = new_value
            
            # Actualizar mensaje de estado
            if new_value < 30:
                self.status_label.config(text="Conectando con nodos...")
            elif new_value < 60:
                self.status_label.config(text="Sincronizando archivos...")
            elif new_value < 90:
                self.status_label.config(text="Verificando integridad...")
            else:
                self.status_label.config(text="¡Listo para comenzar!")
            
            self.after(300, self.update_progress)
        else:
            self.after(500, lambda: self.controller.show_frame("MainScreen"))

class MainScreen(tk.Frame):
    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg=controller.bg_color)
        
        # Inicializar el estado de los nodos
        self.node_status = {}
        self.pending_ops = {}  # Cola de operaciones
        self.node_last_status = {}

        
        self.selected_file = None
        self.selected_node = None
        self.drag_data = {"item": None, "node": None}
        self.create_widgets()
        self.setup_dnd()
        self.update_nodes()

    def open_file(self):
        if not self.selected_file or not self.selected_node:
            messagebox.showwarning("Abrir archivo", "Seleccione un archivo para abrir")
            return

        from client import load_nodes, is_node_alive
        nodes = load_nodes()
        node_key = f"nodo{self.selected_node}"

        if node_key not in nodes:
            messagebox.showerror("Error", f"{node_key} no está disponible en config.json")
            return

        host, port = nodes[node_key]
        if not is_node_alive(host, port):
            # Buscar en respaldo
            respaldo = [(h, p) for n, (h, p) in nodes.items() if n != node_key and is_node_alive(h, p)]
            for rh, rp in respaldo:
                try:
                    r = requests.get(f"http://{rh}:{rp}/shared/{self.selected_file}", timeout=3)
                    if r.status_code == 200:
                        self.show_file_viewer(self.selected_file, r.content.decode())
                        return
                except:
                    continue
            messagebox.showerror("Error", f"{node_key} está desconectado y no se encontró respaldo.")
            return


        try:
            url = f"http://{host}:{port}/shared/{self.selected_file}"
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                if self.selected_file.lower().endswith(".pdf"):
                    # Guardar el archivo temporalmente
                    import tempfile, os, webbrowser
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                        temp_file.write(r.content)
                        temp_path = temp_file.name
                    webbrowser.open_new(temp_path)
                else:
                    content = r.content.decode()
                    self.show_file_viewer(self.selected_file, content)
            else:
                messagebox.showerror("Error", f"No se pudo abrir el archivo: {r.status_code}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")

    def show_file_viewer(self, filename, content):
        viewer = tk.Toplevel(self)
        viewer.title(f"📄 {filename}")
        viewer.geometry("600x400")
        viewer.configure(bg=self.controller.bg_color)

        text_area = tk.Text(viewer, wrap='word', font=('Consolas', 11))
        text_area.insert('1.0', content)
        text_area.pack(expand=True, fill='both', padx=10, pady=10)
        text_area.config(state='disabled')  # Solo lectura

    def create_widgets(self):
        # Barra de control superior
        control_frame = ttk.Frame(self, style='TFrame')
        control_frame.pack(fill='x', padx=10, pady=10)
        # Mostrar nombre del nodo actual arriba
        ttk.Label(self, text=f"🖥 Nodo actual: {self.controller.local_node}", style='Title.TLabel').pack(pady=(10, 0))

        
        # Botones con colores vibrantes
        ttk.Button(
            control_frame, 
            text="Transferir", 
            command=self.transfer_file,
            style='TButton'
        ).pack(side='left', padx=5)
        
        ttk.Button(
            control_frame, 
            text="Eliminar", 
            command=self.delete_file,
            style='TButton'
        ).pack(side='left', padx=5)
        
        ttk.Button(
            control_frame, 
            text="Actualizar", 
            command=self.update_nodes,
            style='TButton'
        ).pack(side='left', padx=5)
        
        ttk.Button(
            control_frame, 
            text="Abrir Archivo", 
            command=self.open_file,
            style='TButton'
        ).pack(side='right', padx=5)

        
        # Contenedor de nodos
        nodes_frame = ttk.Frame(self, style='TFrame')
        nodes_frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.node_frames = {}
        
        # Configurar grid para los 4 nodos
        for i in range(2):
            nodes_frame.grid_rowconfigure(i, weight=1)
            for j in range(2):
                nodes_frame.grid_columnconfigure(j, weight=1)
                node_id = i * 2 + j + 1
                node_frame = self.create_node_frame(nodes_frame, node_id)
                node_frame.grid(row=i, column=j, padx=10, pady=10, sticky="nsew")
                self.node_frames[f"nodo{node_id}"] = node_frame
    
    def create_node_frame(self, parent, node_id):
        node_frame = ttk.Frame(parent, style='Node.TFrame')
        
        # Cabecera del nodo con color de acento
        header_frame = ttk.Frame(node_frame, style='NodeHeader.TFrame')
        header_frame.pack(fill='x')
        
        # Estado del nodo
        #status_label = ttk.Label(header_frame, text="● Conectado", style='Online.TLabel')
        #status_label.pack(side='right', padx=5)
        #node_frame.status_label = status_label
        
        # Título del nodo
        ttk.Label(header_frame, text=f"Nodo {node_id}", style='NodeHeader.TLabel').pack(side='left', padx=5)
        
        # Árbol de archivos
        tree_frame = ttk.Frame(node_frame)
        tree_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Configurar Treeview con estilo personalizado
        style = ttk.Style()
        style.configure("Treeview", 
                       background="#ecf0f1", 
                       fieldbackground="#ecf0f1", 
                       foreground="#2c3e50",
                       rowheight=25)
        style.map('Treeview', background=[('selected', self.controller.secondary_color)])
        
        tree = ttk.Treeview(tree_frame, columns=('size', 'modified'), selectmode='browse')
        tree.heading('#0', text='Nombre')
        tree.heading('size', text='Tamaño')
        tree.heading('modified', text='Modificado')
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        tree.bind('<<TreeviewSelect>>', lambda e, n=node_id: self.on_file_select(e, n))
        
        self.populate_tree(tree, node_id)
        
        node_frame.tree = tree
        node_frame.node_id = node_id
        
        return node_frame
    
    def update_nodes(self):
        from client import load_nodes, is_node_alive, send_file, delete_file
        import requests

        nodes = load_nodes()

        for node_id, frame in self.node_frames.items():
            # Verifica si el nodo está conectado
            if node_id not in nodes:
                status = False
            else:
                host, port = nodes[node_id]
                status = is_node_alive(host, port)

            # Estilo visual
            #label_style = 'Online.TLabel' if status else 'Offline.TLabel'
            #label_text = "● Conectado" if status else "● Desconectado"
            #frame.status_label.configure(style=label_style, text=label_text)

            # Obtener estado anterior (por defecto False)
            last_status = self.node_last_status.get(node_id, False)

            # Si se reconectó, aplicar sincronización y actualizar vista
            if status and last_status is not True:
                print(f"🔌 Nodo {node_id} reconectado.")
                self.populate_tree(frame.tree, frame.node_id)
                #self.aplicar_pendientes(node_id, host, port)  # ← asegúrate de tener esta función

                # Aplicar operaciones pendientes
                if node_id in self.pending_ops:
                    for op in self.pending_ops[node_id]:
                        try:
                            if op['action'] == "delete":
                                delete_file(host, port, op['filename'])
                            elif op['action'] == "transfer":
                                send_file(host, port, op['filename'], op['content'])  # asegúrate de guardar 'content' también
                        except Exception as e:
                            print(f"[!] Error aplicando operación pendiente: {e}")
                    
                    # Eliminar operaciones pendientes solo si no fallaron
                    del self.pending_ops[node_id]
                    print(f"[✔] Operaciones pendientes aplicadas a {node_id}")

            # Si está conectado y no hubo cambio, refrescar si lo deseas
            elif status:
                self.populate_tree(frame.tree, frame.node_id)

            # Guardar nuevo estado para la próxima iteración
            self.node_last_status[node_id] = status
            



    def simulate_failure(self):
        node_id = random.randint(1, 4)
        node_key = f"nodo{node_id}"
        current_status = self.node_status[node_key]
        new_status = not current_status
        
        self.node_status[node_key] = new_status
        action = "desconectado" if not new_status else "reconectado"
        messagebox.showinfo("Simulación de Fallo", f"Nodo {node_id} {action}")
        self.update_nodes()
    
    def on_file_select(self, event, node_id):
        tree = event.widget
        selected_item = tree.selection()
        if selected_item:
            parts = []
            current = selected_item[0]
            while current:
                parts.insert(0, tree.item(current, 'text'))
                current = tree.parent(current)

            self.selected_file = "/".join(parts)
            self.selected_node = node_id

            tags = tree.item(selected_item[0], 'tags')
            self.selected_is_folder = "folder" in tags


    def transfer_file(self):
        if not self.selected_file or not self.selected_node:
            messagebox.showwarning("Transferencia", "Seleccione un archivo y un nodo destino")
            return
        
        dest_window = tk.Toplevel(self)
        dest_window.title("Seleccionar Nodo Destino")
        dest_window.geometry("300x200")
        dest_window.configure(bg=self.controller.bg_color)
        
        ttk.Label(dest_window, text="Seleccione nodo destino:", style='TLabel').pack(pady=10)
        
        from client import load_nodes, is_node_alive
        nodes = load_nodes()

        for node_id in range(1, 5):
            if node_id == self.selected_node:
                continue

            node_key = f"nodo{node_id}"
            label = f"Nodo {node_id}"
            estado = "conectado" if node_key in nodes and is_node_alive(*nodes[node_key]) else "desconectado"

            ttk.Button(
                dest_window,
                text=f"{label} ({estado})",
                command=lambda n=node_id: self.confirm_transfer(n, dest_window),
                style='TButton'
            ).pack(pady=5)

        
        #ttk.Label(dest_window, text="O arrastre el archivo al nodo destino", style='TLabel').pack(pady=10)

    def confirm_transfer(self, dest_node, window):
        from client import load_nodes, send_file, is_node_alive, send_folder
        import requests, os

        window.destroy()

        if not messagebox.askyesno("Confirmar Transferencia", f"¿Transferir '{self.selected_file}' a Nodo {dest_node}?", icon='question'):
            return

        nodes = load_nodes()
        origen_key = f"nodo{self.selected_node}"
        destino_key = f"nodo{dest_node}"

        if origen_key not in nodes or destino_key not in nodes:
            messagebox.showerror("Error", "Nodos no encontrados en la configuración")
            return

        origen_host, origen_port = nodes[origen_key]
        destino_host, destino_port = nodes[destino_key]

        # Si es carpeta, usar send_folder directamente desde disco
        # Si es carpeta, usar send_folder directamente desde disco
        if self.selected_is_folder:
            try:
                otros = [(h, p) for n, (h, p) in nodes.items() if n != destino_key and is_node_alive(h, p)]
                respaldo = otros[:1]
                send_folder(destino_host, destino_port, self.selected_file, replicate_to=respaldo)
                messagebox.showinfo("Transferencia Exitosa", f"Carpeta '{self.selected_file}' transferida a Nodo {dest_node}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo transferir carpeta: {e}")
            return  # ✅ Esto evita que siga tratando la carpeta como archivo


        # Si destino no está vivo, registrar como pendiente
        if not is_node_alive(destino_host, destino_port):
            self.pending_ops.setdefault(destino_key, []).append({
                "action": "transfer",
                "filename": self.selected_file,
                "source": origen_key
            })
            messagebox.showinfo("Pendiente", f"La transferencia se programó para cuando {destino_key} se reconecte.")
            return

        # Obtener nodos disponibles para respaldo
        otros = [(h, p) for n, (h, p) in nodes.items() if n != destino_key and n != origen_key and is_node_alive(h, p)]
        respaldo = otros[:1]

        # Primero, intentar obtener el archivo desde el origen (si está vivo)
        if is_node_alive(origen_host, origen_port):
            try:
                r = requests.get(f"http://{origen_host}:{origen_port}/shared/{self.selected_file}", timeout=5)
                if r.status_code == 200:
                    content = r.content
                    send_file(destino_host, destino_port, self.selected_file, content=content, replicate_to=respaldo)
                    messagebox.showinfo("Transferencia Exitosa", f"Archivo '{self.selected_file}' transferido a Nodo {dest_node}")
                    return
            except Exception as e:
                print(f"[!] Error al obtener desde {origen_key}: {e}")

        # Si el origen está desconectado o falló, buscar el archivo en respaldo
        for alt_node, (h, p) in nodes.items():
            if alt_node in [origen_key, destino_key]:
                continue
            if is_node_alive(h, p):
                try:
                    r = requests.get(f"http://{h}:{p}/shared/{self.selected_file}", timeout=5)
                    if r.status_code == 200:
                        content = r.content
                        send_file(destino_host, destino_port, self.selected_file, content=content, replicate_to=respaldo)
                        messagebox.showinfo("Transferencia Exitosa", f"Archivo obtenido desde {alt_node} y enviado a Nodo {dest_node}")
                        return
                except Exception as e:
                    print(f"[!] Error al buscar en respaldo {alt_node}: {e}")
                    continue

        # Si no se pudo transferir de ninguna forma
        messagebox.showerror("Error", f"No se pudo obtener el archivo desde {origen_key} ni desde respaldos.")


    def delete_file(self):
        from client import load_nodes, is_node_alive, delete_file as real_delete

        if not self.selected_file or not self.selected_node:
            messagebox.showwarning("Eliminar", "Seleccione un archivo para eliminar")
            return

        nodes = load_nodes()
        node_key = f"nodo{self.selected_node}"

        if not is_node_alive(*nodes.get(node_key, ["", 0])):
            # Agregar a la cola de operaciones
            self.pending_ops.setdefault(node_key, []).append({"action": "delete", "filename": self.selected_file})
            messagebox.showinfo("Pendiente", f"La eliminación de '{self.selected_file}' se programó para {node_key}")

            # Quitar visualmente del árbol de archivos
            tree = self.node_frames[node_key].tree
            for item in tree.get_children():
                if tree.item(item, "text") == self.selected_file:
                    tree.delete(item)
                    break

            return

        if messagebox.askyesno("Confirmar Eliminación", f"¿Eliminar '{self.selected_file}' del Nodo {self.selected_node}?", icon='warning'):
            host, port = nodes[node_key]
            real_delete(host, port, self.selected_file)
            messagebox.showinfo("Eliminación Exitosa", f"Archivo '{self.selected_file}' eliminado del Nodo {self.selected_node}")
            self.update_nodes()

    

    def populate_tree(self, tree, node_id):
        tree.delete(*tree.get_children())
        from client import load_nodes
        import requests

        nodes = load_nodes()
        node_key = f"nodo{node_id}"

        if node_key not in nodes:
            tree.insert('', 'end', text=f"[Nodo {node_key} no registrado]")
            return

        host, port = nodes[node_key]
        try:
            url = f"http://{host}:{port}/list_tree"
            r = requests.get(url, timeout=5)
            data = r.json()

            def insert_node(parent, item):
                node = tree.insert(parent, 'end', text=item["name"], values=(item.get("size", ""), item.get("modified", "")))
                for child in item.get("children", []):
                    insert_node(node, child)

            for item in data:
                insert_node('', item)

        except Exception as e:
            tree.insert('', 'end', text=f"[Error al cargar: {e}]")


        
    def setup_dnd(self):
        for frame in self.node_frames.values():
            tree = frame.tree
            tree.bind('<ButtonPress-1>', self.drag_start)
            tree.bind('<B1-Motion>', self.drag_motion)
            tree.bind('<ButtonRelease-1>', self.drag_end)
    
    def drag_start(self, event):
        tree = event.widget
        item = tree.identify_row(event.y)
        if item:
            parent = tree
            while parent is not None and not hasattr(parent, "node_id"):
                parent = parent.master

            if parent is not None and hasattr(parent, "node_id"):
                self.drag_data = {"item": item, "node": parent.node_id}
            else:
                self.drag_data = {"item": None, "node": None}

    
    def drag_motion(self, event):
        pass
    
    def drag_end(self, event):
        if not self.drag_data["item"]:
            return
        
        widget = event.widget.winfo_containing(event.x_root, event.y_root)
        while widget and not hasattr(widget, 'node_id'):
            widget = widget.master
        
        if widget and hasattr(widget, 'node_id'):
            source_node = self.drag_data["node"]
            dest_node = widget.node_id
            file_name = event.widget.item(self.drag_data["item"], 'text')
            
            if source_node != dest_node and self.node_status[f"nodo{dest_node}"]:
                if messagebox.askyesno(
                    "Transferir Archivo", 
                    f"¿Transferir '{file_name}' al Nodo {dest_node}?",
                    icon='question'
                ):
                    messagebox.showinfo(
                        "Transferencia Exitosa", 
                        f"Archivo '{file_name}' transferido a Nodo {dest_node}"
                    )
        
        self.drag_data = {"item": None, "node": None}

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()