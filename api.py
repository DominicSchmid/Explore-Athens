import datetime as dt
import os
import requests
import json
import sys

from flask_restful import Api, Resource, reqparse
from flask import Flask, send_from_directory, make_response

import mysql.connector
from mpu import haversine_distance

"""
-------------------------------
| Dominic Schmid - 05.04.2018 |
-------------------------------
"""

errors = {
    'File not found': {
        'message': 'File not found',
        'status': 404
    }
}

app = Flask(__name__)
api = Api(app, errors=errors, catch_all_404s=True)

MAPS_KEY = "5b3ce3597851110001cf62482e2890bc9f8e432886b7708caecd04e2"
MAPS_URL = "https://api.openrouteservice.org/v2/directions/foot-walking"

WEATHER_KEY = "0a187d268a9951e269589ac49f41a67c"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
ICON_URL = "http://openweathermap.org/img/w/"

ADMIN_KEY = "12345"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
HOST = "0.0.0.0"  # 10.10.30.9:5053

IMG_DIR = "images"
IMAGES = {}

# TODO query from db to select all sites and load them into the python program
# NOTE on export bring dependencies!


""" Response Codes
200 OK, 201 Created, 204 No Content
400 Bad Request (Syntax), 401 Unauthorized (No Key), 403 Forbidden, 404 Not Found
"""

# Global sites array containing all sites at runtime
sites = []


def read_config():
    """Read the config file and initialize the variables"""
    if os.path.exists("config.json"):
        with open("config.json") as f:
            config = json.load(f)

    try:
        MAPS_KEY = config["maps_key"]
        MAPS_URL = config["maps_url"]
        WEATHER_KEY = config["weather_key"]
        WEATHER_URL = config["weather_url"]
        FORECAST_URL = config["forecast_url"]
        ICON_URL = config["icon_url"]
        ADMIN_KEY = config["admin_key"]
        DATETIME_FORMAT = config["datetime_format"]
        DATE_FORMAT = config["date_format"]
        TIME_FORMAT = config["time_format"]
        IMG_DIR = config["img_dir"]
        HOST = config["host"]
        print("Read configuration successfully!")
    except Exception as e:
        print("Fatal error: 'config.json' was not found or has errors: {}".format(e))
        exit(1)


class WeatherNow(Resource):

    """Class for handling requests to /weather/now\n
    Supports ``GET``"""

    def get(self, place=None):
        """Get weather at certain place.\n
        If place is empty place defaults to 'Athens,GR'

        Args:
            place (str): The location to get the weather for

        Returns:
            a dict of the current weather conditions in a specified place
        """
        if place is None:
            place = "Athens,GR"

        res = requests.get(
            WEATHER_URL, {"q": place, "appid": WEATHER_KEY, "units": "metric"})

        code = res.status_code
        res = res.json()  # Convert to JSON object to read data
        if code == 200:
            return {
                "name": res["name"],
                "date": get_date(),
                "time": get_time(),
                "min_temp": float(res["main"]["temp_min"]),
                "max_temp": float(res["main"]["temp_max"]),
                "temp": float(res["main"]["temp"]),  # Temp in C
                "humidity": float(res["main"]["humidity"]),  # Percentage
                "icon": res["weather"][0]["icon"],  # Image ID for png
                "description": res["weather"][0]["description"]
            }, 200, {"response-type": "weathernow"}
        return {"message": "{}".format(res["message"])}, res["cod"]


class WeatherForecast(Resource):

    """Class for handling requests to /weather/forecast\n
    Supports ``GET``"""

    def get(self, place=None):
        """Get weatherforecast at certain place.\n
        If place is empty place defaults to 'Athens,GR'

        Args:
            place (str): The location to get the weatherforecast for

        Returns:
            a dict of the weatherforecast for a specified place
        """
        if place is None:
            place = "Athens,GR"

        res = requests.get(
            FORECAST_URL, {"q": place, "appid": WEATHER_KEY, "units": "metric"})  # 4 Tage

        code = res.status_code
        res = res.json()  # Convert to JSON object to read data

        if code == 200:
            res_list = res["list"]
            forecast = {
                "name": place,
                "date": get_date(),
                "time": get_time(),
                "forecast": []
            }

            for f in res_list:
                forecast["forecast"].append({
                    "min_temp": float(f["main"]["temp_min"]),
                    "max_temp": float(f["main"]["temp_max"]),
                    "temp": float(f["main"]["temp"]),  # Temp in C
                    "humidity": float(f["main"]["humidity"]),  # Percentage
                    "icon": f["weather"][0]["icon"],  # Image ID for png
                    "description": f["weather"][0]["description"],
                    "dt_txt": f["dt_txt"]
                })
            return forecast, 200, {"response-type": "weatherforecast"}
        return {"message": "{}".format(res["message"])}, res["cod"]


class Sites(Resource):

    """Class for handling requests to /sites\n
    Supports ``GET``"""

    def get(self, x=None, y=None, radius=5):
        """Gets all sites or sites in a certain radius from a given coordinate. Defaults to 5 kilometers.\n

        Args:
            x (float): X coordinate of the user NOTE: Must be a float eg. 2.0
            y (float): Y coordinate of the user NOTE: Must be a float eg. 2.0
            radius (float): Radius (kilometers) in which sites should be added to the result array
        Returns:
            a json object of the list of sites within a given radius of the users position.
        """
        # If called sites without arguments
        parser = reqparse.RequestParser()
        parser.add_argument("name")
        parser.add_argument("lan")
        parser.add_argument("radius")
        args = parser.parse_args()

        if args["lan"] is None:
            language = "de"
        else:
            language = args["lan"]

        renew_sites(language)

        if x is None and y is None:
            # No need to react to radius parameter if two coordinates were given
            # If sites called and no name is given then return all sites
            if args["name"] is None:
                return sites, 200, {"response-type": "sites"}

            # Else return all sites with matching name substrings
            new_sites = []
            for site in sites:
                if args["name"].lower() in site["name"].lower():
                    new_sites.append(site)

            if new_sites:  # If array is not empty
                return new_sites, 200, {"response-type": "sites"}
            return {"message": "Site not found!"}, 404

        # Use specified radius if radius is given
        if args["radius"] is not None:
            radius = float(args["radius"])

        sites_in_radius = []

        for site in sites:
            # Get distance in kilometers and check if site is inside radius
            distance = haversine_distance((site["x"], site["y"]), (x, y))
            # print("Distance between ({}/{}) and ({}/{}): {:.4f}km".format(
            #    site["x"], site["y"], x, y, distance))
            if distance <= radius:
                site["distance"] = distance
                sites_in_radius.append(site)

        if sites_in_radius:  # If array not empty
            return sites_in_radius, 200, {"response-type": "sites"}
        return {"message": "No points of interest found within a {}km radius of {}/{}".format(radius, x, y)}, 404


class Position(Resource):

    """Class for handling requests to /position\n
    Supports ``POST``"""

    def post(self, uid):
        """Writes position to remote database for the given name

        Args:
            name (str): The name of the person to write the new position for

        Returns:
            a string and the corresponding HTTP status code
        """
        parser = reqparse.RequestParser()
        parser.add_argument("x")
        parser.add_argument("y")
        args = parser.parse_args()

        if args["x"] is None or args["y"] is None:
            return {"message": "Coordinates not specified correctly!"}, 400

        return add_position(uid, args["x"], args["y"])


class Route(Resource):

    """Class for handling requests to /route\n
    Supports ``GET``"""

    def get(self, start, end, write_to_file=False):
        """Get route from point A to point B by foot NOTE: Float params must be a float eg. 2.0

        Args:
            start (float): Start position formatted as lat,lon
            end (float): End position formatted as lat,lon

        Returns:
            a JSON object containing all the directions from A to B
        """
        res = requests.get(
            MAPS_URL, {"api_key": MAPS_KEY, "start": start, "end": end})

        if res.status_code == 200:
            res = res.json()

            if write_to_file:  # TODO Remove later
                with open("dir.json", "w") as f:
                    json.dump(res, f, indent=4)

            return res, 200, {"response-type": "route"}
        return {"message": "Route could not be calculated!", "code": "{}".format(res.text)}, 400


class Image(Resource):

    """Class for handling requests to /image\n
    Supports ``GET``"""

    def get(self, path):
        """Sends an image to the client

        Args:
            path (str): The name of the image to download

        Returns:
            a byte string or directly downloads a file if opened in the browser
        """
        try:
            extension = os.path.splitext(path)[1]
            response = make_response(send_from_directory(IMG_DIR, path, as_attachment=True))
            response.headers["response-type"] = "image"
            response.status_code = 200
            return response
            # return send_from_directory(IMG_DIR, IMAGES[path], as_attachment=True), 200, {"response-type": "image", "extension": extension}
        except Exception as e:
            return {"message": "Image not found"}, 404


class AdminSite(Resource):

    """Testing"""

    def post(self, name):
        """Adds a new site with the specified parameters"""
        parser = reqparse.RequestParser()
        parser.add_argument("key")
        parser.add_argument("address")
        parser.add_argument("x")
        parser.add_argument("y")
        parser.add_argument("description")
        args = parser.parse_args()

        if args["key"] != ADMIN_KEY:
            return {"message": "Invalid key!"}, 401

        if args["address"] is None or args["x"] is None or args["y"] is None or args["description"] is None:
            return {"message": "You must specify all variables!"}, 400

        for site in sites:
            if site["name"].lower() == name.lower():
                # Site exists, change info that is different TODO alter table
                site["address"] = args["address"]
                site["x"] = float(args["x"])
                site["y"] = float(args["y"])
                site["description"] = args["description"]
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
            return {"message": "Invalid key!"}, 401

        for site in sites:
            if site["name"].lower() == name.lower():
                # TODO remove from database
                print("Removed ", name)

                return {"success": "Removed {}!".format(name)}, 200

        return {"message": "Site not found!"}, 404


def db_connect():
    """Connects to database

    Returns:
        an instance of a MySQL Connection
    """
    try:
        cnx = mysql.connector.connect(user="root", password="mysql#5BT", host="localhost",
                                      database="python", auth_plugin="mysql_native_password")  # TODO database python
    except Exception as e:
        print("Database connection error:")
        print(e)
        print("The application was started but it may not function correctly.")
        return None

    return cnx


def renew_sites(language):
    """Updates site array with newest sites by fetching all from mysql database"""

    try:
        cnx = db_connect()
        cursor = cnx.cursor()
        query = "SELECT s_name, s_address, s_x, s_y, s_description, s_image1, s_image2, s_image3 FROM sites JOIN siteinfo{} ON sites.s_id = siteinfo{}.s_id".format(
            language, language)
        cursor.execute(query)

        # Update all known sites
        sites.clear()
        for entry in cursor.fetchall():
            # Name, Address, X, Y, Description
            sites.append({
                "name": entry[0],
                "address": entry[1],
                "x": entry[2],
                "y": entry[3],
                "description": entry[4],
                "images": [
                    entry[5],
                    entry[6],
                    entry[7]
                ]
            })
        cnx.close()  # Close due to resource leakage
    except Exception as e:
        print("Error trying to fetch Sites")
        print(e)


def add_position(user, x, y):
    """Add new position for a given user to the database made by another group
    Args:
        user (string): The android ID of the person
        x (float): The new x coordinate
        y (float): The new y coordinate

    Returns:
        a string and HTTP status code for answering the API request
    """
    try:
        standort_url = "185.5.199.33:5051/addLocation"
        res = requests.post("{}/{}/{}/{}".format(standort_url, user, x, y))
        if res.status_code == 200:
            return {"success": "Position added successfully!"}, 201
        else:
            return {"message": json.loads(res.content)}, res.status_code
    except Exception as e:
        print("Destination server unreachable")
        return {"message": "Destination server did not respond! Please wait and hope for the best"}, 400


def get_date():
    """Get current date in a given format"""
    return dt.datetime.now().strftime(DATE_FORMAT)


def get_time():
    """Get current time in a given format"""
    return dt.datetime.now().strftime(TIME_FORMAT)


# You must call as a float 2.0 or you will get a 404 error
api.add_resource(Sites, "/sites", "/sites/<float:x>/<float:y>", "/sites/<int:x>/<int:y>", endpoint="sites")
api.add_resource(WeatherNow, "/weather/now", "/weather/now/<string:place>", endpoint="weathernow")
api.add_resource(WeatherForecast, "/weather/forecast",
                 "/weather/forecast/<string:place>", endpoint="weatherforecast")
api.add_resource(Position, "/position/<string:uid>")
api.add_resource(Route, "/route/<string:start>/<string:end>")
api.add_resource(AdminSite, "/site/<string:name>")
api.add_resource(Image, "/image/<string:path>")


read_config()
renew_sites("de")

# app.run(host="0.0.0.0")
# If cmd line arguments passed use first argument as host IP
if len(sys.argv) > 0:
    try:
        HOST = sys.argv[1]
        print("Argument detected and using as host ip: {}".format(HOST))
    except:
        pass

if HOST == "localhost":
    app.run(debug=True)
else:
    app.run(host=HOST)


# app.run(debug=True)
# TODO change database to support image paths, change this code to send image paths in response
# TODO do not use run in a production environment, check function documentations
