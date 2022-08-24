import enum
from instagrapi import Client
from dotenv import load_dotenv
import io
import os
import tempfile
from PIL import Image
from dotenv import load_dotenv

load_dotenv()


class InstaBot:
    def __init__(self):
        self.cl = Client()
        self.cl.login(os.getenv('instaUser'), os.getenv('instaPass'))
        print("Insta bot running")

    def uploadAlbum(self, files, id, caption):
        paths = []
        
        for count, file in enumerate(files):
            Image.open(io.BytesIO(file.fp.getbuffer())).convert("RGB").save(f"scripts/toSend/{count}-image_scaled.jpg",quality=95)
            paths.append(f"scripts/toSend/{count}-image_scaled.jpg")
        
        
        media = self.cl.album_upload(
            paths,
            caption,
        )
        
        print(f"Album is uploaded - {caption}")
        # return media.pk
        return "test"

    def deleteAlbum(self, path):
        print(f"Album deleted - {path}")
