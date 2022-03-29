import requests


class BasicAuth:
    def __init__(self, user, token):
        self.session = requests.Session()
        self.user = user
        self.token = token
