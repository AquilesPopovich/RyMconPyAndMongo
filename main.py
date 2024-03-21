import requests
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import io
import pymongo
from bson.objectid import ObjectId


# Variables de configuración de MongoDB
MONGO_HOST = "localhost"
MONGO_PORT = 27017
MONGO_TIMEOUT = 2000
MONGO_URL = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/"

MONGO_BASEDEDATOS = "rym"
MONGO_COLECCION = "personajes"

# Conexión a MongoDB
client = pymongo.MongoClient(MONGO_URL, serverSelectionTimeoutMS=MONGO_TIMEOUT)
coleccion = client[MONGO_BASEDEDATOS][MONGO_COLECCION]

# Variables globales
ID_CHARACTER = ""
PERSONAJE_SELECCIONADO = False

def mostrarPersonajesAPI():
    try:
        URL = 'https://rickandmortyapi.com/api/character'
        limit = 2
        offset = 0
        url_con_parametros = f'{URL}?limit={limit}&offset={offset}'
        response = requests.get(url_con_parametros)

        if response.status_code == 200:
            data = response.json()
            for personaje in data['results']:
                crear_tarjeta(personaje['id'], personaje['name'], personaje['status'], personaje['image'])
        else:
            print(f'Error al realizar la solicitud: {response.status_code}')
    except requests.exceptions.RequestException as e:
        print("Error de conexión con la API:", e)

def mostrarPersonajesMongo():
    # Eliminar todas las tarjetas actuales en el main_frame
    for widget in main_frame.winfo_children():
        widget.destroy()

    try:
        personajes = coleccion.find()
        for personaje in personajes:
            crear_tarjeta(personaje['_id'], personaje['name'], personaje['status'], personaje['image'])
    except pymongo.errors.ConnectionFailure as errorConexion:
        print("Fallo al conectarse a MongoDB ", errorConexion)

def crear_tarjeta(character_id, name, status, image_url):
    card_frame = ttk.Frame(main_frame)
    card_frame.pack(side=tk.LEFT, padx=10, pady=10)

    label_name = ttk.Label(card_frame, text=f'Name: {name}')
    label_name.pack()

    label_status = ttk.Label(card_frame, text=f'Status: {status}')
    label_status.pack()

    image_data = requests.get(image_url).content
    image = Image.open(io.BytesIO(image_data))
    image = ImageTk.PhotoImage(image.resize((150, 150)))
    label_image = ttk.Label(card_frame, image=image)
    label_image.image = image  # Necesario para mantener la referencia a la imagen
    label_image.pack()

    # Botón Seleccionar
    select_button = ttk.Button(card_frame, text="Seleccionar", command=lambda id=character_id: dobleClickBtn(id))
    select_button.pack()

def mostrarBotones():
    global PERSONAJE_SELECCIONADO
    print('hola')
    if PERSONAJE_SELECCIONADO:
        crear_button.pack_forget()
        editar_button.pack()
        delete_button.pack()
    else:
        editar_button.pack_forget()
        delete_button.pack_forget()
        crear_button.pack()

def dobleClickBtn(character_id):
    global ID_CHARACTER, PERSONAJE_SELECCIONADO
    ID_CHARACTER = character_id

    # Verificar si el personaje está en la base de datos local
    personajeSeleccionado = coleccion.find_one({'_id': character_id})
    if personajeSeleccionado:
        cargarDatosPersonaje(personajeSeleccionado)
    else:
        try:
            # Obtener los datos del personaje de la API
            URL = f'https://rickandmortyapi.com/api/character/{ID_CHARACTER}'
            response = requests.get(URL)
            data = response.json()
            if data: 
             cargarDatosPersonaje(data)
             PERSONAJE_SELECCIONADO = True
            mostrarBotones()
        except requests.exceptions.RequestException as e:
            print("Error al obtener la información del personaje:", e)

def cargarDatosPersonaje(data):
    name_entry.delete(0, tk.END)
    name_entry.insert(tk.END, data['name'])
    status_entry.delete(0, tk.END)
    status_entry.insert(tk.END, data['status'])
    species_entry.delete(0, tk.END)
    species_entry.insert(tk.END, data.get('species', ''))
    gender_entry.delete(0, tk.END)
    gender_entry.insert(tk.END, data.get('gender', ''))
    image_entry.delete(0, tk.END)
    image_entry.insert(tk.END, data['image'])

def crear_registro():
    name = name_entry.get()
    status = status_entry.get()
    species = species_entry.get()
    gender = gender_entry.get()
    image = image_entry.get()

    if name and status and species and gender and image:
        try:
            new_character = {
                "_id": ID_CHARACTER,  # Utilizamos '_id' como clave para el ID
                "name": name,
                "status": status,
                "species": species,
                "gender": gender,
                "image": image
            }
            coleccion.insert_one(new_character)
            name_entry.delete(0, tk.END)
            status_entry.delete(0, tk.END)
            species_entry.delete(0, tk.END)
            gender_entry.delete(0, tk.END)
            image_entry.delete(0, tk.END)
            mostrarPersonajesMongo()
        except pymongo.errors.ConnectionFailure as errorConexion:
            print("Fallo al conectarse a MongoDB ", errorConexion)
    else:
        messagebox.showerror(message="Los campos no pueden estar vacíos")

def eliminarPersonaje():
    global ID_CHARACTER
    eliminado = coleccion.delete_one({'_id': ObjectId(ID_CHARACTER)})
    if eliminado: 
        mostrarPersonajesMongo()
        mostrarPersonajesAPI()
    else: messagebox.showerror(message="no puedes eliminar un personaje de la api")

def editarPersonaje():
    global ID_CHARACTER
    name = name_entry.get()
    status = status_entry.get()
    species = species_entry.get()
    gender = gender_entry.get()
    image = image_entry.get()

    if name and status and species and gender and image:
        try:
            idPersonaje = {'_id': ObjectId(ID_CHARACTER)}
            valoresNuevos = {
                 "name": name,
                 "status": status,
                 "species": species,
                 "gender": gender,
                 "image": image
            }
            coleccion.update_one(idPersonaje, {"$set": valoresNuevos})
            name_entry.delete(0, tk.END)
            status_entry.delete(0, tk.END)
            species_entry.delete(0, tk.END)
            gender_entry.delete(0, tk.END)
            image_entry.delete(0, tk.END)
        except pymongo.errors.ConnectionFailure as errorConexion:
            print("Fallo al conectarse a MongoDB ", errorConexion)
    else:
        messagebox.showerror(message="Los campos no pueden estar vacíos")
    mostrarPersonajesMongo()
    mostrarPersonajesAPI()

# Crear la interfaz gráfica
root = tk.Tk()
root.title("Personajes de Rick and Morty")

# Crear un marco principal para las tarjetas
main_frame = ttk.Frame(root)
main_frame.pack(padx=20, pady=20)

# Crear campos de entrada para mostrar la información del personaje seleccionado
name_label = ttk.Label(root, text="Name:")
name_label.pack()
name_entry = ttk.Entry(root)
name_entry.pack()

status_label = ttk.Label(root, text="Status:")
status_label.pack()
status_entry = ttk.Entry(root)
status_entry.pack()

species_label = ttk.Label(root, text="Species:")
species_label.pack()
species_entry = ttk.Entry(root)
species_entry.pack()

gender_label = ttk.Label(root, text="Gender:")
gender_label.pack()
gender_entry = ttk.Entry(root)
gender_entry.pack()

image_label = ttk.Label(root, text="Image URL:")
image_label.pack()
image_entry = ttk.Entry(root)
image_entry.pack()

crear_button = ttk.Button(root, text="Crear Personaje", command=crear_registro)
crear_button.pack()

editar_button = ttk.Button(root, text="Editar Personaje", command=editarPersonaje)
delete_button = ttk.Button(root, text="Eliminar Personaje", command=eliminarPersonaje)

# Mostrar los personajes de la API de Rick and Morty y de MongoDB al inicio
mostrarPersonajesMongo()
mostrarPersonajesAPI()

root.mainloop()
