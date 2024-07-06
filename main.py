import asyncio
import json
import requests
import websockets
from requests_toolbelt.multipart.encoder import MultipartEncoder
import speech_recognition as sr

import threading
import tkinter as tk
from tkinter import scrolledtext

from animation import generate_animation

selected_workspace_id = "667ee8bc3a6ab5948b8a5321"

work_path = "C:/UTEC/ComputacionGrafica/Proyecto/Proyecto-Computacion-Grafica/"
blender_infile_path = f"{work_path}mcqueen.blend"
blender_outfile_path = f"{work_path}mcqueen_mod.blend"
rendering_path = f"{work_path}render/"
audio_path = f"{work_path}audio.mp3"
animation_path = f"{work_path}animation.mp4"

# Función para obtener el token de conexión
def get_token():
    url = f"https://entiendo-workspaces.azurewebsites.net/api/workspaces/{selected_workspace_id}/token"
    response = requests.get(url)
    return response.json()


# Función para manejar la conexión de WebSocket
async def connect_and_listen(websocket_url, text_widget):
    async with websockets.connect(websocket_url) as websocket:
        # text_widget.insert(tk.END, "🚀 Connection is connected.\n")
        # text_widget.see(tk.END)
        print("🚀 Connection is connected.\n")

        async for message in websocket:
            data = json.loads(message)
            if "data" in data:
                text = json.loads(data)['data']['text']
                text_widget.insert(tk.END, f"Mcqueen: {json.loads(data)['data']['text']}\n")
                text_widget.see(tk.END)
                return text

async def handle_group_message(data):
    # Aquí puedes manejar el mensaje del grupo similar a tu código JavaScript
    print(f"Handling group message: {data}")
    # ... (tu lógica para manejar mensajes de grupo)


def upload_text_resource(name, text, workspace_id):
    # Crear el objeto FormData
    form_data = MultipartEncoder(
        fields={
            'name': name,
            'text': text
        }
    )

    # URL de la API
    url = f"https://entiendo-workspaces-api.azure-api.net/workspaces/{workspace_id}/texts"

    # Opciones de la petición
    headers = {
        'Content-Type': form_data.content_type
    }
    response = requests.post(url, data=form_data, headers=headers)

    # Verificar si la respuesta es exitosa
    response.raise_for_status()

    # Obtener los datos de la respuesta en formato JSON
    data = response.json()
    return data


def generate_chat(data):
    url = 'https://entiendo-chat-with-gpt-premium.azurewebsites.net/api/chat'
    # url = 'http://localhost:7071/api/chat'  # Si deseas usar un servidor local

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()  # Verificar si la petición fue exitosa

        # Obtener la respuesta en formato JSON
        generate_chat_output = response.json()
        return generate_chat_output
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def grabar_y_transcribir(text_widget):
    # Crear un reconocedor de audio
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        # print("Por favor, hable ahora...")
        text_widget.insert(tk.END, "Please, speak now\n")
        text_widget.see(tk.END)

        # Ajustar el nivel de ruido ambiental
        recognizer.adjust_for_ambient_noise(source)

        # Grabar el audio
        audio = recognizer.listen(source)

        # print("Grabación completa, procesando...")
        text_widget.insert(tk.END, "Transcription complete, processing\n")
        text_widget.see(tk.END)
    try:
        # Usar Google Web Speech API para reconocer el audio
        # recognizer.recognize_amazon(audio)
        texto = recognizer.recognize_google(audio, language='es-ES')
        # print(f"Transcripción: {texto}")
        text_widget.insert(tk.END, f"You: {texto}\n")
        text_widget.see(tk.END)
    except sr.UnknownValueError:
        print("No se pudo entender el audio")
    except sr.RequestError as e:
        print(f"Error al solicitar resultados del servicio de reconocimiento de voz; {e}")

    return texto


def foo(text):
    print("FOO>", text)

async def main(text_widget):
    texto = grabar_y_transcribir(text_widget)
    res = upload_text_resource(name="name", workspace_id=selected_workspace_id, text=f"responde el siguiente texto en ingles como si fueras el rayo mcqueen de una forma breve, dame solo la respuesta: {texto}")
    # print(res)

    data = {
        "name": "name",
        "resource": {
            "resourceId": f"{res['id']}",
            "workspaceId": f"{selected_workspace_id}"
        },
        "options": {
            "lang": "es"
        }
    }
    result = generate_chat(data)
    # if result:
    #     print("Generate chat output:", result)

    token_data = get_token()
    websocket_url = token_data['url']
    text = await connect_and_listen(websocket_url, text_widget)
    text = 'Hi'
    print(text)
    #foo(text)
    generate_animation(text, blender_infile_path, blender_outfile_path, rendering_path, audio_path, animation_path)



def start_program(text_widget):
    asyncio.run(main(text_widget))

def run_in_thread(func, *args):
    thread = threading.Thread(target=func, args=args)
    thread.start()

def create_gui():
    root = tk.Tk()
    root.title("McQueen App")

    text_widget = scrolledtext.ScrolledText(root, width=80, height=20)
    text_widget.pack(padx=10, pady=10)

    start_button = tk.Button(root, text="Speak", command=lambda: run_in_thread(start_program, text_widget))
    start_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    create_gui()
