import requests
import json

class Client:

    def __init__(self, client_id):
        self.client_id = client_id

    def get(self, url, data):
        header = {"Client-ID": str(self.client_id)}
        req = requests.get("https://api.twitch.tv/helix/{}".format(url), params=data, headers=header)
        return req.json()

    def __getattr__(self, item):
        item = item.replace("_", "/")
        return (lambda data : self.get(item, data))
