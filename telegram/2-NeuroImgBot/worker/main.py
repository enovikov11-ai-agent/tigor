from torch import autocast
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline
import requests
from io import BytesIO
from PIL import Image, ImageOps
import time
import os
import json


with open('./secrets.json') as secrets_file:
    secrets = json.load(secrets_file)

txt2img = None
img2img = None

def telegram(method, data = None, files = None):
    response = requests.post(f"https://api.telegram.org/bot{secrets['TELEGRAM_API_KEY']}/{method}", data = data, files = files)
    return json.loads(response.text)

def delete_message(chat_id, message_id):
    telegram("deleteMessage", {'chat_id': chat_id, 'message_id': message_id})

def send_message(chat_id, text, reply_to_message_id):
    result_json = telegram("sendMessage", {'chat_id': chat_id, 'text': text, 'reply_to_message_id': reply_to_message_id, 'disable_notification': True})
    return result_json['result']['message_id']

def send_photos(chat_id, images, caption, reply_to_message_id):
    if len(images) == 1:
        telegram("sendPhoto", {'chat_id': chat_id, 'caption': caption, 'reply_to_message_id': reply_to_message_id}, {'photo': ('image.png', images[0], 'image/png')})
    else:
        media = []
        files = {}
        for i in range(len(images)):
            files["photo" + str(i)] = ('image' + str(i) + '.png', images[i], 'image/png')

            media_item = {'type': 'photo', 'media': "attach://photo" + str(i)}

            if i == 0:
                media_item['caption'] = caption

            media.append(media_item)
        
        telegram("sendMediaGroup", {'chat_id': chat_id, 'reply_to_message_id': reply_to_message_id, 'media': json.dumps(media)}, files)

def get_photo(file_id, file_unique_id):
    file_json = telegram("getFile", {'file_id': file_id, 'file_unique_id': file_unique_id})
    file_body = requests.get(f"https://api.telegram.org/file/bot{secrets['TELEGRAM_API_KEY']}/{file_json['result']['file_path']}")
    return Image.open(BytesIO(file_body.content))

def process(text):
    global txt2img
    global img2img

    task = json.loads(text)
    if task is None:
        return
    
    is_image = "requestPhoto" in task

    if is_image:
        if not img2img:
            if txt2img:
                txt2img.to("cpu")
            img2img = StableDiffusionImg2ImgPipeline.from_pretrained("CompVis/stable-diffusion-v1-4", use_auth_token=True)
    else:
        if not txt2img:
            if img2img:
                img2img.to("cpu")
            txt2img = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4", use_auth_token=True)

    print("Model loaded " + str(time.time()))

    delete_message(task["chatId"], task["enqueuedMessageId"])
    processing_message = send_message(task["chatId"], 'Processing', task["messageId"])

    if txt2img:
        txt2img.to("cpu" if is_image else "cuda")
    
    if img2img:
        img2img.to("cuda" if is_image else "cpu")

    print("Model loaded to gpu " + str(time.time()))

    images = []

    with autocast("cuda"):
        for i in range(task["count"]):
            if is_image:
                init_image = get_photo(task["requestPhoto"]["fileId"], task["requestPhoto"]["fileUniqueId"])
                thumb = ImageOps.fit(init_image, (512, 512), Image.ANTIALIAS)
                image = img2img(prompt = task["request"], init_image = thumb, strength = task["strength"], num_inference_steps = task["steps"], guidance_scale = task["scale"]).images[0]
            else:
                image = txt2img(prompt = task["request"], num_inference_steps = task["steps"], guidance_scale = task["scale"]).images[0]
            
            byte_io = BytesIO()
            image.save(byte_io, 'png')
            byte_io.seek(0)
            images.append(byte_io)

    send_photos(chat_id = task["chatId"], images = images, caption = task["origRequest"], reply_to_message_id = task["messageId"])    
    delete_message(task["chatId"], processing_message)

    print("Processing finished " + str(time.time()))

print("Loop started " + str(time.time()))

try:
    while True:
        response = requests.get(f"{secrets['SERVER_BASE']}{secrets['SERVER_SECRET']}/get-task-longpoll?worker={os.environ['WORKER_ID']}", timeout=90)
        if response.status_code == 200:
            print("Processing request " + str(time.time()) + " " + response.text)
            try:
                process(response.text)
            except Exception as e:
                print(e)
        else:
            break
except Exception as e:
    print(e)

print("Notify stopped " + str(time.time()))
try:
    requests.get(f"{secrets['SERVER_BASE']}{secrets['SERVER_SECRET']}/notify-stopped?worker={os.environ['WORKER_ID']}", timeout=15)
except Exception as e:
    print(e)

print("Shutting down " + str(time.time()))
os.system("sudo shutdown now -h")