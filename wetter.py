import requests
import json

URL = 'https://api.openrouteservice.org/v2/directions/foot-walking'
MAPS_KEY = "5b3ce3597851110001cf62482e2890bc9f8e432886b7708caecd04e2"

start = "8.681495,49.41461"
end = "8.687872,49.420318"

res = requests.get(URL, {"api_key": MAPS_KEY, "start": start, "end": end})

print(res.json())
with open("dir.json", "w") as f:
    json.dump(res.json(), f, indent=4)
