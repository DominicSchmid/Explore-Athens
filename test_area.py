import requests

URL = "http://127.0.0.1:5000"

req = requests.get(URL + "/image/img.jpg", {"Content-Type": "multiplart/form-data"})

with open("recved.jpg", "wb") as f:
    # print(req.text)
    f.write(req.content)
