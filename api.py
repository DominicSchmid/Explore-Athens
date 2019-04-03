from flask_restful import Api, Resource, reqparse
from math import sin, cos, sqrt, atan2, radians
from flask import Flask
import mysql.connector
import datetime as dt
import requests
import json
import mpu


app = Flask(__name__)
api = Api(app)

MAPS_KEY = "5b3ce3597851110001cf62482e2890bc9f8e432886b7708caecd04e2"
MAPS_URL = "https://api.openrouteservice.org/v2/directions/foot-walking"

WEATHER_KEY = "0a187d268a9951e269589ac49f41a67c"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
ICON_URL = "http://openweathermap.org/img/w/"

ADMIN_KEY = "12345"

# TODO query from db to select all sites and load them into the python program
# NOTE on export bring dependencies!


""" Response Codes
200 OK, 201 Created, 204 No Content
400 Bad Request (Syntax), 401 Unauthorized (No Key), 403 Forbidden, 404 Not Found
"""

sites = [
    {
        "name": "Akropolis",
        "address": "Max Mustermannstrasse 1",
        "x": 37.9715326,
        "y": 23.7257335,
        "description": "Das ist die Akropolis"
    },
    {
        "name": "Bonzata",
        "address": "Max Sonnleiten 21",
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

        code = res.status_code
        res = res.json()  # Convert to JSON object to read data
        if code == 200:
            return {
                "name": res["name"],
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
            return "Error: {}".format(res["message"]), res["cod"]


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
        # If called sites without arguments
        if x is None and y is None:
            parser = reqparse.RequestParser()
            parser.add_argument("name")
            args = parser.parse_args()

            # If sites called and ?name is not found return all sites
            if args["name"] is None:
                return json.dumps(sites), 200

            # Else return all sites with matching substrings
            new_sites = []
            for site in sites:
                if args["name"].lower() in site["name"].lower():
                    new_sites.append(site)

            if len(new_sites) > 0:
                return json.dumps(new_sites), 200
            else:
                return "Error: Site not found!", 404

        parser = reqparse.RequestParser()
        parser.add_argument("radius")
        args = parser.parse_args()

        if args["radius"] is not None:
            radius = float(args["radius"])

        print("Radius:", radius)
        sites_in_radius = []
        # TODO SQL query to get all sites

        for site in sites:
            # Get distance in kilometers and check if site is inside radius
            distance = self.get_distance(site["x"], site["y"], x, y)
            print(
                "Distance between ({}/{}) and ({}/{}): {:.4f}km".format(site["x"], site["y"], x, y, distance))
            if distance < radius:
                site["distance"] = distance
                sites_in_radius.append(site)

        if len(sites_in_radius) > 0:
            return json.dumps(sites_in_radius, indent=4), 200
        else:
            return "No points of interest found within a radius of {}km".format(radius), 404


class Position(Resource):

    """
    Get position for Person
    """

    def get(self, name):
        # TODO query to select newest positions for person
        return "No positions found for {}".format(name), 200

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
            if name.lower() == user["name"].lower():
                # TODO add new entry to Database here
                print("New entry for {} added: ({}/{})".format(name,
                                                               args["x"], args["y"]))
                user["x"] = args["x"]
                user["y"] = args["y"]
                user["date"] = dt.datetime.now().strftime("%x")
                user["time"] = dt.datetime.now().strftime("%X")
                return user, 201

        # TODO Maybe create user if not exists
        return "User does not exist!", 404


class Route(Resource):

    """
    Get Route from point a to point b by foot
    :param start Coordinate in format x.xx,y.yy
    :param end Coordinate in format x.xx,y.yy
    :return Returns the directions from A to B or Error 400
    """

    def get(self, start, end, write_to_file=False):
        #start = "8.681495,49.41461"
        #end = "8.687872,49.420318"

        res = requests.get(
            MAPS_URL, {"api_key": MAPS_KEY, "start": start, "end": end})

        if res.status_code == 200:
            res = res.json()

            if write_to_file:  # TODO Remove later
                with open("dir.json", "w") as f:
                    json.dump(res, f, indent=4)

            return res, 200
        else:
            return "Error: Route could not be calculated!\nError: {}".format(res.text()), 400


class AdminSite(Resource):

    def post(self, name):
        parser = reqparse.RequestParser()
        parser.add_argument("key")
        parser.add_argument("address")
        parser.add_argument("x")
        parser.add_argument("y")
        parser.add_argument("description")
        args = parser.parse_args()

        if args["key"] != ADMIN_KEY:
            return "Error: Invalid key!", 401

        if args["address"] is None or args["x"] is None or args["y"] is None or args["description"] is None:
            return "Error: You must specify all variables!", 400

        for site in sites:
            if site["name"].lower() == name.lower():
                # Site exists, change info that is different TODO alter table
                site["address"] = args["address"]
                site["x"]: float(args["x"])
                site["y"]: float(args["y"])
                site["description"]: args["description"]
                return "{} updated successfully!".format(name), 200

        # TODO database create new item
        d = {
            "name": name,
            "address": args["address"],
            "x": float(args["x"]),
            "y": float(args["y"]),
            "description": args["description"]
        }
        # append to array
        return json.dumps(d), 200

    def delete(self, name):
        parser = reqparse.RequestParser()
        parser.add_argument("key")
        args = parser.parse_args()

        if args["key"] != ADMIN_KEY:
            return "Error: Invalid key!", 401

        for site in sites:
            if site["name"].lower() == name.lower():
                # TODO remove from database
                print("Removed ", name)

                return "Removed {}!".format(name), 200

        return "Error: Site not found!", 404


"""
Connect to all the databases needed for the program
"""


def db_connect():
    cnx = mysql.connector.connect(
        user="root", password="mysql#5BT", host="localhost", database="test")

    return cnx
    """cursor = cnx.cursor()

    cursor.execute("CREATE TABLE test(vorname VARCHAR(255))")
    cnx.close()"""


# Can call /sites or /sites/x/y. First returns all sites, second sites in radius
api.add_resource(
    Sites, "/sites", "/sites/<float:x>/<float:y>", endpoint="sites")
api.add_resource(Weather, "/weather",
                 "/weather/<string:place>", endpoint="weather")
api.add_resource(Position, "/position/<string:name>")
api.add_resource(Route, "/route/<string:start>/<string:end>")
api.add_resource(AdminSite, "/site/<string:name>")
app.run(debug=True)
