import pyowm

KEY = "0a187d268a9951e269589ac49f41a67c"

owm = pyowm.OWM(KEY, language="de")  # You MUST provide a valid API key

# Search for current weather in London (Great Britain)
#j = owm.get_json_at_place("London,GB")
print(owm)
observation = owm.weather_at_place('London,GB')
w = observation.get_weather()
print(w)
