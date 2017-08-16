from flask import Flask, request, render_template
import flask
import parser
import csv
import json
import os
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)


def load_config(filename):
    ''' Return a config dict from given JSON filename
    '''
    with open(filename, 'r') as config:
        return json.load(config)


@app.route('/index.js')
def index_js():
    locations = parser.get_all_coordinates()
    images = parser.get_all_images()
    clusters = parser.get_all_clusters()
    return flask.render_template("index.js",
                                 locations=locations,
                                 images=images,
                                 clusters=clusters,
                                 base_url=os.environ['STATIC_URL_BASE'])


@app.route('/')
def index():
    return flask.render_template("index.html",
                                 ACCESS_KEY=load_config('/config/config.json')['GOOGLE_MAP_KEY'])


@app.route("/api/coordinates/v1.0/", methods=['POST'])
def post():
    message = request.form['Body']
    parsed = parser.parse_message(message)
    resp = MessagingResponse()
    if parsed != 0:
        # Add the coordinates to our local coordinates file
        with open(r'/data/coordinates.csv', 'a') as f:
            writer = csv.writer(f)
            writer.writerow(parsed)
        return str(resp), 200
    else:
        return str(resp), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
