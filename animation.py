import bpy
from gtts import gTTS
import nltk
from nltk.corpus import cmudict
import string
from moviepy.editor import ImageSequenceClip, AudioFileClip
import requests
import os

#nltk.download('cmudict')

phonetic_to_animation = {
    'AA': "m_AEI",
    'AH': "m_AEI",
    'AW': "m_AEI",
    'B': "m_BMP",
    'D': "m_CDGKRSTXZ",
    'EH': "m_AEI",
    'EY': "m_AEI",
    'G': "m_CDGKRSTXZ",
    'IH': "m_AEI",
    'JH': "m_JChSh",
    'L': "m_L",
    'N': 'm_N',
    'OW': "m_O",
    'P': "m_BMP",
    'S': "m_CDGKRSTXZ",
    'T': "m_CDGKRSTXZ",
    'UH': 'm_U',
    'V': "m_FV",
    'Y': "m_JChSh",
    'ZH': "m_JChSh",
    'AE': "m_AEI",
    'AO': "m_AEI",
    'AY': "m_AEI",
    'CH': "m_JChSh",
    'DH': "m_CDGKRSTXZ",
    'ER': "m_AEI",
    'F': "m_FV",
    'HH': "m_JChSh",
    'IY': "m_AEI",
    'K': "m_CDGKRSTXZ",
    'M': "m_BMP",
    'NG': 'm_N',
    'OY': "m_O",
    'R': "m_CDGKRSTXZ",
    'SH': "m_JChSh",
    'TH': "m_Th",
    'UW': "m_U",
    'W': "m_QW",
    'Z': "m_CDGKRSTXZ"
}

def path_to_write(path, filename, extension = None):
    counter = 1
    while True:
        if extension:
            file_name = f"{filename}_{counter}.{extension}"
        else:
            file_name = f"{filename}_{counter}/"
        file_path = os.path.join(path, file_name)
        if not os.path.exists(file_path):
            break
        counter += 1
    return file_path

def cleanse_num(string_list):
    return [s.translate(str.maketrans('', '', '0123456789')) for s in string_list]

def get_phonetics(phrase):
    d = cmudict.dict()
    translator = str.maketrans('', '', string.punctuation)
    cleaned_phrase = phrase.translate(translator)
    words = cleaned_phrase.lower().split()

    phonetic_transcriptions = []
    for word in words:
        if word in d:
            phonetic_transcriptions.append(cleanse_num(d[word][0]))
        else:
            phonetic_transcriptions.append("No transcription available for this word.")
    return phonetic_transcriptions

def text_to_speech(text, path):
    obj = {
        "text": text,
        "speaker": "00157155-3826-11ee-a861-00163e2ac61b",
        "emotion": "Enthusiastic"
    }
    url = "https://api.topmediai.com/v1/text2speech"
    api_key = "9a366a4de10c42eaa54990aa74aa9518"
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=obj, headers=headers)
        response.raise_for_status() 
        audio_url = response.json()["data"]["oss_url"]
        with open(path, "wb") as file:
            audio_response = requests.get(audio_url)
            file.write(audio_response.content)
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar o recibir la solicitud: {e}")

def modify_shape_key(obj_name, shape_key_name, frame_number, new_value):
    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        print(f"Object '{obj_name}' not found.")
        return
    if not obj.data.shape_keys:
        print(f"Object '{obj_name}' has no shape keys.")
        return
    shape_key = obj.data.shape_keys.key_blocks.get(shape_key_name)
    if shape_key is None:
        print(f"Shape key '{shape_key_name}' not found.")
        return

    bpy.context.scene.frame_set(frame_number)
    shape_key.value = new_value
    shape_key.keyframe_insert(data_path="value", frame=frame_number)

def run_animations(animation, frame):
    modify_shape_key("body", animation, frame, 0.0)
    frame += 6
    modify_shape_key("body", animation, frame, 1.0)
    modify_shape_key("body", animation, frame + 3, 0.0)
    frame += 0
    return frame

def generate_animation(text, blender_infile_path, blender_outfile_path, rendering_path, audio_path, animation_path):
    phonetic_transcriptions = get_phonetics(text)

    audio_path_w = path_to_write(audio_path, 'audio', 'wav')
    text_to_speech(text, audio_path_w)

    bpy.ops.wm.open_mainfile(filepath=blender_infile_path)
    frame = 0
    for word in phonetic_transcriptions:
        for phon in word:
            if phon != "HH":
                animations = phonetic_to_animation.get(phon, None)
                if animations:
                    frame = run_animations(animations, frame)
        frame += 6

    bpy.data.scenes[0].frame_end = frame
    bpy.ops.wm.save_as_mainfile(filepath=blender_outfile_path)

    bpy.ops.wm.open_mainfile(filepath=blender_outfile_path)
    bpy.data.scenes[0].render.engine = "CYCLES"

    bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "OPTIX"
    bpy.context.scene.cycles.device = "GPU"
    bpy.context.preferences.addons["cycles"].preferences.get_devices()

    print(bpy.context.preferences.addons["cycles"].preferences.compute_device_type)
    for d in bpy.context.preferences.addons["cycles"].preferences.devices:
        d["use"] = 1 # Using all devices, include GPU and CPU
        print(d["name"], d["use"])

    rendering_path_w = path_to_write(rendering_path, 'render')
    bpy.data.scenes[0].render.filepath = rendering_path_w
    bpy.ops.render.render(animation=True)

    image_files = [f'{rendering_path_w}{i:04d}.png' for i in range(frame+1)]

    audio = AudioFileClip(audio_path_w)
    audio_duration = audio.duration
    adjusted_fps = int((frame + 1) / audio_duration)
    clip = ImageSequenceClip(image_files, fps=adjusted_fps)
    clip = clip.set_audio(audio)
    animation_path_w = path_to_write(animation_path, 'animation', 'mp4')
    clip.write_videofile(animation_path_w, codec='libx264', audio_codec='aac')
