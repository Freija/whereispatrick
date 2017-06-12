from flask import Flask, current_app, jsonify, request, render_template, redirect
from flask_restful import Resource, Api, abort, reqparse
import flask
import settings
import parser
import csv
import datetime

app = Flask(__name__)
api = Api(app)

@app.route('/')
def index():
    locations = parser.get_all_coordinates()
    return flask.render_template(
                                "index.html",
                                ACCESS_KEY = settings.GOOGLE_MAP_KEY,
                                locations = locations
                                )

class coordinateAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('message',
                                   type=str,
                                   help='Iridium text message')
    def put(self):
        message = request.form['data']
        parsed = parser.parse_message(message)
        if parsed != 0:
            # Add the coordinates to our local coordinates file
            with open(r'./app/coordinates.csv', 'a') as f:
                writer = csv.writer(f)
                writer.writerow(parsed)
            return 'OK'
        else:
            return 'FAIL'

api.add_resource(coordinateAPI, '/api/coordinates/v1.0/')

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
