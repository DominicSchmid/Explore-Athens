import requests
import json

from flask_restful import Api, Resource
from flask import Flask, send_file, send_from_directory
import io

app = Flask(__name__)
api = Api(app)


@app.route("/image/<string:path>")
def get(path):
    """image_binary = read_image(path)
    return send_file(io.BytesIO(image_binary), mimetype='image/png', as_attachment=True,
                        attachment_filename='%s.png' % path)"""
    return send_from_directory("images", path, as_attachment=True)


#api.add_resource(Image, "/image/<string:path>")
app.run(debug=True)
