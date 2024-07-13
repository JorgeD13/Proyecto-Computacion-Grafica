import asyncio
import json
import requests
import websockets
from requests_toolbelt.multipart.encoder import MultipartEncoder
import speech_recognition as sr

from animation import generate_animation

selected_workspace_id = "667ee8bc3a6ab5948b8a5321"

work_path = "C:/UTEC/ComputacionGrafica/Proyecto/Proyecto-Computacion-Grafica/"
blender_infile_path = f"{work_path}blend/mcqueen_trans.blend"
blender_outfile_path = f"{work_path}blend/mcqueen_mod.blend"
rendering_path = f"{work_path}renders/"
audio_path = f"{work_path}audios/"
animation_path = f"{work_path}animations/"

def get_token():
    url = f"https://entiendo-workspaces.azurewebsites.net/api/workspaces/{selected_workspace_id}/token"
    response = requests.get(url)
    return response.json()

async def connect_and_listen(websocket_url):
    async with websockets.connect(websocket_url) as websocket:
        print("🚀 Connection established.")
        async for message in websocket:
            data = json.loads(message)
            if "data" in data:
                text = json.loads(data)['data']['text']
                print(text)
                generate_animation(text, blender_infile_path, blender_outfile_path, rendering_path, audio_path, animation_path)

def upload_text_resource(name, text, workspace_id):
    form_data = MultipartEncoder(
        fields={
            'name': name,
            'text': text
        }
    )
    url = f"https://entiendo-workspaces-api.azure-api.net/workspaces/{workspace_id}/texts"
    headers = {
        'Content-Type': form_data.content_type
    }
    response = requests.post(url, data=form_data, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data

def generate_chat(data):
    url = 'https://entiendo-chat-with-gpt-premium.azurewebsites.net/api/chat'
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        generate_chat_output = response.json()
        return generate_chat_output
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def grabar_y_transcribir():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Please, speak now...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
        print("Processing...")
    try:
        texto = recognizer.recognize_google(audio, language='es-ES')
        print(f"Transcription: {texto}")
    except sr.UnknownValueError:
        print("Couldn't recognize audio")
    except sr.RequestError as e:
        print(f"Error requesting voice recognition service; {e}")
    return texto

async def main():
    texto = grabar_y_transcribir()
    res = upload_text_resource(name="name", workspace_id=selected_workspace_id, text=f"responde el siguiente texto en español como si fueras el rayo mcqueen de forma breve, dame solo la respuesta:{texto}")
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
    token_data = get_token()
    websocket_url = token_data['url']
    await connect_and_listen(websocket_url)

if __name__ == "__main__":
    asyncio.run(main())
