from instagrapi import Client
from dotenv import load_dotenv
import os

class InstaBot:
    def __init__(self):
        # self.cl = Client()
        # self.cl.login(os.getenv('instaUser'), os.getenv('instaPass'))
        print("Insta bot running")

    def uploadAlbum(self, paths, caption):
        print(f"Album is uploaded - {paths} - {caption}")
        # self.cl.album_upload(
        #     paths,
        #     caption,
        # )
        return "https://www.reddit.com/r/AskReddit/"

    def deleteAlbum(self, path):
        print(f"Album deleted - {path}")
