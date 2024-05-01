import os
import requests
import datetime
import base64


class Github:
    def __init__(self):
        self.token = base64.b64decode("Z2hwX2pYUU5YY0dEZ3dPNm9WTVJuYUgxR2FGUVZ3eG9OZDIyaUtCNg==")
        self.org = "coursedio"
        
    def upload(self, filepath, uploadpath, repo):
        headers = {
            "content-type": "application/json",
            "authorization": f"token {self.token}",
            "accept": "application/vnd.github+json",
        }
        with open(filepath, "rb") as source_file:
            encoded_string = base64.b64encode(source_file.read()).decode("utf-8")

        payload = {
            "message": f"Uploaded file at {datetime.datetime.now().isoformat()}",
            "content": encoded_string,
        }

        requests.put(
            f"https://api.github.com/repos/{self.org}/{repo}/contents/{uploadpath}",
            json=payload,
            headers=headers,
        )
    
    def create_repo(self, name):
        r = requests.post(f"https://api.github.com/orgs/{self.org}/repos", json={
            "name": name,
            "private": False
        }, headers={
            "content-type": "application/json",
            "authorization": f"token {self.token}",
            "accept": "application/vnd.github+json",
        })
        if "name" not in r.json():
            return None
        return name
    
    