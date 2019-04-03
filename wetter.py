import requests

ATHENS_ID = 264371
KEY = "0a187d268a9951e269589ac49f41a67c"
#URL = "api.openweathermap.org/data/2.5/weather?"
# Search for current weather in London (Great Britain)
#j = owm.get_json_at_place("London,GB")
URL = "https://api.openweathermap.org/data/2.5/weather"
# Add imagecode and .png ie. /w/02d.png
IMG_URL = "http://openweathermap.org/img/w/"

# req = requests.get(URL, {"id": ATHENS_ID, "appid"})
req = requests.get(
    URL, {"q": "Athens,GR", "appid": KEY, "units": "metric"}).json()
icon_id = req["weather"][0]["icon"]
temperature = req["main"]["temp"]
humidity = req["main"]["humidity"]
weather = req["weather"]
print(req)
print(icon_id)
print(temperature)
print(humidity)
