# OSLink

**OSLink** es un sistema distribuido con tolerancia a fallas que permite la interconexión de múltiples nodos (computadoras). Los nodos pueden realizar operaciones como transferir y eliminar archivos entre ellos. El sistema está diseñado para ser escalable, permitiendo añadir tantos nodos como se desee.

## 🚀 Características

- Arquitectura distribuida con tolerancia a fallas.
- Transferencia y eliminación de archivos entre nodos.
- Escalabilidad: añade tantos nodos como necesites.
- Interfaz gráfica intuitiva para gestionar los nodos y operaciones.

## 🛠️ Requisitos previos

- Python 3 instalado en tu sistema.
- Git (opcional, para clonar el repositorio).

## ⚙️ Instalación

### En sistemas Linux/macOS:

1. Clona el repositorio (si aún no lo has hecho):

   ```bash
   git clone https://github.com/tu_usuario/OSLink.git
   cd OSLink
   ```

2. Crea un entorno virtual:

   ```bash
   python3 -m venv .venv
   ```

3. Activa el entorno virtual:

   ```bash
   source .venv/bin/activate
   ```

4. Instala las dependencias necesarias:

   ```bash
   pip install Flask requests
   ```

### En sistemas Windows:

1. Clona el repositorio (si aún no lo has hecho):

   ```cmd
   git clone https://github.com/tu_usuario/OSLink.git
   cd OSLink
   ```

2. Crea un entorno virtual:

   ```cmd
   python -m venv .venv
   ```

3. Activa el entorno virtual:

   ```cmd
   .venv\Scripts\activate
   ```

4. Instala las dependencias necesarias:

   ```cmd
   pip install Flask requests
   ```

## 🔧 Configuración del nodo

Antes de iniciar el nodo, debes configurar su identificador y puerto. Edita el archivo `Nodo/Distribuido/Backend/app.py` y modifica las siguientes líneas según tus preferencias:

```python
my_id = "nodo4"
my_port = "5004"
```

- `my_id`: Identificador único para el nodo (por ejemplo, "nodo1", "nodo2", etc.).
- `my_port`: Puerto en el que el nodo escuchará las solicitudes.

Asegúrate de que cada nodo tenga un `my_id` y `my_port` únicos para evitar conflictos.

## 🖥️ Interfaz gráfica

Una vez configurados y añadidos los nodos al sistema, puedes utilizar la interfaz gráfica para gestionar y operar sobre ellos. La interfaz se encuentra en el archivo `Nodo/Distribuido/Frontend/interfaz.py`.

Para iniciar la interfaz gráfica, ejecuta:

```bash
python Nodo/Distribuido/Frontend/interfaz.py
```

La interfaz te permitirá realizar operaciones como:

- Visualizar el estado de los nodos.
- Transferir archivos entre nodos.
- Eliminar archivos en nodos específicos.
- Añadir o eliminar nodos del sistema.

## 🚀 Uso

Una vez configurado el nodo y la interfaz gráfica, puedes iniciar la aplicación ejecutando:

```bash
python Nodo/Distribuido/Backend/app.py
```

El nodo estará listo para interactuar con otros nodos en la red, permitiendo la transferencia y eliminación de archivos.

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Si deseas mejorar OSLink, por favor sigue estos pasos:

1. Haz un fork del repositorio.
2. Crea una nueva rama (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y haz commit (`git commit -m 'Agrega nueva funcionalidad'`).
4. Haz push a la rama (`git push origin feature/nueva-funcionalidad`).
5. Abre un Pull Request.

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más información.
