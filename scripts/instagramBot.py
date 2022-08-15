from instagrapi import Client

class InstaBot:
    def __init__(self):
        self.cl = Client()
        self.cl.login("interestingredditreadit", "yeKta2000?!?")

    def uploadAlbum(self, paths, caption):
        self.cl.album_upload(
            paths,
            caption,
        )