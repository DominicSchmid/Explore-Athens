import requests
import json

from flask_restful import Api, Resource
from flask import Flask, send_file, send_from_directory
import io

app = Flask(__name__)
api = Api(app)


@app.route("/image/<string:path>")
def get(path):
    return send_from_directory("images", path, mimetype="image/png", as_attachment=True)


#api.add_resource(Image, "/image/<string:path>")
app.run(debug=True)
