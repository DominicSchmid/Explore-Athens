from flask_restful import Api, Resource, reqparse
from math import sin, cos, sqrt, atan2, radians
from flask import Flask
import datetime as dt
import requests
import json
import mpu


app = Flask(__name__)
api = Api(app)

MAPS_KEY = "5b3ce3597851110001cf62482e2890bc9f8e432886b7708caecd04e2"
WEATHER_KEY = "0a187d268a9951e269589ac49f41a67c"

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
ICON_URL = "http://openweathermap.org/img/w/"

# GET für Koordinaten, Rechne entfernung zu POI aus
# POST für standort schicken und in DB schreiben
# TODO query from db to select all sites and load them into the python program
# NOTE on export bring dependencies!


""" Response Codes
200 OK, 201 Created, 204 No Content
400 Bad Request (Syntax), 401 Unauthorized (No Key), 403 Forbidden, 404 Not Found
"""

sites = [
    {
        "name": "Akropolis",
        "adress": "Max Mustermannstrasse 1",
        "x": 37.9715326,
        "y": 23.7257335,
        "description": "Das ist die Akropolis"
    },
    {
        "name": "Bonzata",
        "adress": "Max Sonnleiten 21",
        "x": 37.9215326,
        "y": 23.7557335,
        "description": "Das ist ein anderes Point of Interest!"
    }
]

users = [
    {
        "id": 1,
        "name": "Dominic"
    }
]


class Weather(Resource):

    """
    GET Weather at certain place
    :return Returns a dict of the current weather conditions in a specified palce
    If place is not specified Athens,GR will be used
    """

    def get(self, place=None):
        if place is None:
            place = "Athens,GR"

        res = requests.get(
            WEATHER_URL, {"q": place, "appid": WEATHER_KEY, "units": "metric"})

        if res.status_code == 200:
            res = res.json()  # Convert to JSON object to read data

            return {
                "place": res["name"],
                "date": dt.datetime.now().strftime("%X"),
                "time": dt.datetime.now().strftime("%x"),
                "min_temp": res["main"]["temp_min"],
                "max_temp": res["main"]["temp_max"],
                "temp": res["main"]["temp"],  # Temp in °C
                "humidity": res["main"]["humidity"],  # Percentage
                "icon": res["weather"][0]["icon"],  # Image ID for png
                "description": res["weather"][0]["description"]
            }
        else:
            return "Error: Getting weather from OpenWeatherMap failed!"


class Sites(Resource):

    """
    Calculate the distance between two coordinates on a sphere
    """
    @staticmethod
    def get_distance(lat1, lon1, lat2, lon2):
        return mpu.haversine_distance((lat1, lon1), (lat2, lon2))

    """
    GET request to either get all sites or sites in a certain radius from a coordinate
    :param x: X coordinate of the user
    :param y: Y coordinate of the user
    :return Returns a json object of the list of sites within a given radius of the users position
    Radius: Radius (kilometers) in which sites should be added to the result array
    """

    def get(self, x=None, y=None, radius=5):
        if x is None and y is None:
            return sites

        print("Radius:", radius)
        sites_in_radius = []
        # TODO SQL query to get all sites

        for site in sites:
            # Distance in kilometers
            distance = self.get_distance(site["x"], site["y"], x, y)
            print(
                "Distance between ({}/{}) and ({}/{}): {:.4f}km".format(site["x"], site["y"], x, y, distance))
            if distance < radius:
                site["distance"] = distance
                sites_in_radius.append(site)

        if len(sites_in_radius) > 0:
            return json.dumps(sites_in_radius, indent=4), 201
        else:
            return "Error: There are no points of interest within a radius of {}".format(radius), 404


class Position(Resource):

    """
    Get position for Person
    """

    def get(self, name):
        # TODO query to select newest positions for person
        return "No positions found for {} ".format(name), 204

    """
    Write position to database under this name
    """

    def post(self, name):
        parser = reqparse.RequestParser()
        parser.add_argument("x")
        parser.add_argument("y")
        args = parser.parse_args()

        if args["x"] is None and args["y"] is None:
            return "No coordinates specified!", 400

        for user in users:
            if name == user["name"]:
                # TODO add new entry to Database here
                print("New entry for {} added: ({}/{})".format(name,
                                                               args["x"], args["y"]))
                user["x"] = args["x"]
                user["y"] = args["y"]
                return user, 201

        # TODO Maybe create user if not exists
        return "User does not exist!", 404


# Can call /sites or /sites/x/y. First returns all sites, second sites in radius
api.add_resource(Sites, "/sites", "/sites/<float:x>/<float:y>",
                 "/sites/<float:x>/<float:y>/<float:radius>", endpoint="sites")
api.add_resource(Weather, "/weather",
                 "/weather/<string:place>", endpoint="weather")
api.add_resource(Position, "/position/<string:name>")
app.run(debug=True)
