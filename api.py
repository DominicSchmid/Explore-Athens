from flask import Flask
from flask_restful import Api, Resource, reqparse
import json
import pyowm
import datetime as dt
from math import sin, cos, sqrt, atan2, radians
import mpu

app = Flask(__name__)
api = Api(app)

MAPS_KEY = "5b3ce3597851110001cf62482e2890bc9f8e432886b7708caecd04e2"
WEATHER_KEY = "0a187d268a9951e269589ac49f41a67c"

# OWM docs https://media.readthedocs.org/pdf/pyowm/latest/pyowm.pdf
# GET für Koordinaten, Rechne entfernung zu POI aus
# POST für standort schicken und in DB schreiben
# TODO query from db to select all sites and load them into the python program

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


class Weather(Resource):

    """
    GET Weather at certain place
    """

    def get(self, place="Athens,GR"):
        # You MUST provide a valid API key
        owm = pyowm.OWM(WEATHER_KEY, language="de")
        w = owm.weather_at_place(place).get_weather()

        d = {
            "place": place,  # string
            # Datetime Object
            "time": w.get_reference_time("date").strftime("%x %X"),
            # dict w/ cur max min
            "temperature": w.get_temperature(unit="celsius"),
            "cloud_percentage": w.get_clouds(),  # Number
            "cloud_status": w.get_detailed_status()  # String e.g. bewölkt
        }

        return d


class AllSites(Resource):

    # Returns all known sites as json
    def get(self):
        return json.dumps(sites), 201

    # TODO def post(self, ARGS) to add new site


class Sites(Resource):

    @staticmethod
    def get_distance(lat1, lon1, lat2, lon2):
        return mpu.haversine_distance((lat1, lon1), (lat2, lon2))

    """
    GET Request
    :param x: X coordinate of the user
    :param y: Y coordinate of the user
    :return Returns a json object of the list of sites within a given radius of the users position
    Radius: Radius (kilometers) in which sites should be added to the result array
    """

    def get(self, x, y, radius=5):
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


"""
class User(Resource):

    # Normale Get Anfrage, wenn der User existiert returne den User
    def get(self, name):
        for user in users:
            if name == user["name"]:
                return user, 200
        return "User not found", 404

    # POST Anfrage, erstellt neuen User mit Parametern oder gibt Fehler zurück wenn es ihn schon gibt
    def post(self, name):
        parser = reqparse.RequestParser()
        parser.add_argument("age")
        parser.add_argument("occupation")
        args = parser.parse_args()

        for user in users:
            if name == user["name"]:
                return "User with name {} already exists".format(name), 400

        user = {
            "name": name,
            "age": args["age"],
            "occupation": args["occupation"]
        }

        users.append(user)
        return user, 201

    # PUT ändert bereits existierenden User oder erstellt ihn neu
    def put(self, name):
        parser = reqparse.RequestParser()
        parser.add_argument("age")
        parser.add_argument("occupation")
        args = parser.parse_args()

        for user in users:
            if name == user["name"]:
                user["age"] = args["age"]
                user["occupation"] = args["occupation"]
                return user, 200

        user = {
            "name": name,
            "age": args["age"],
            "occupation": args["occupation"]
        }

        users.append(user)
        return user, 201

    # Entfernt User
    def delete(self, name):
        global users
        users = [user for user in users if user["name"] != name]
        return "{} is deleted.".format(name), 200"""


api.add_resource(Sites, "/sites/<int:x>/<int:y>")
api.add_resource(AllSites, "/allsites")
api.add_resource(Weather, "/weather/<string:place>")
app.run(debug=True)
