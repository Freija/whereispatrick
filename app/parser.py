from datetime import datetime
import re
import csv


def nospace(input_string):
    ''' return the given string with all spaces removed '''
    return input_string.replace(" ", "")


def deg_min_sec_todeg(deg, min, sec):
    ''' This function will return degrees from degrees, minutes, seconds.
    Arguments:
        Three strings: degrees, minutes, seconds of location
    '''
    # Keep track if we have negative degrees
    is_neg = deg.startswith('-')
    degrees = abs(int(nospace(deg))) + int(min)/60.0 + int(sec)/3600.0
    if is_neg:
        return -1 * degrees
    else:
        return degrees


def parse_message(message):
    ''' This function will check if the posted message is valid and then
    proceed to parse it to produce a coordinate data-point.
    Arguments:
        message  -- input message that needs to be checked.
    '''
    result = []
    message_regex = re.compile(r'^'
                               r'Lat([0-9\s\-]+)deg(\d+)\'(\d+)\"\s'
                               r'Lon([0-9\s\-]+)deg(\d+)\'(\d+)\"\s'
                               r'Alt[+-](\d+)\s\w{1,3}\s'
                               r'\(.+?\sago\)\s'
                               r'(\d{2}-[A-Za-z]{3}-\d{4}\s'
                               r'\d{2}:\d{2}:\d{2})\sUTC\s'
                               r'.+'
                               r'$')
    matches = message_regex.match(message)
    if matches:
        lat_deg = matches.group(1)
        lat_min = matches.group(2)
        lat_sec = matches.group(3)
        lon_deg = matches.group(4)
        lon_min = matches.group(5)
        lon_sec = matches.group(6)
        result.append(deg_min_sec_todeg(lat_deg, lat_min, lat_sec))
        result.append(deg_min_sec_todeg(lon_deg, lon_min, lon_sec))
        result.append(int(matches.group(7)))
        result.append(datetime.strptime(matches.group(8),'%d-%b-%Y %H:%M:%S'))
        return result
    else:
        return 0


def get_all_coordinates():
    ''' This function will retrieve the coordinates from the local csv file.
    Arguments:
        None
    '''
    result = []
    with open('/data/coordinates.csv', 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            result.append(row)
    return result


def make_feature(coordinate, order):
    ''' This function will assemble and return a json GEO point, ready to be
    used by Mapbox.
    Arguments:
        A coordinate as a list: [lat, lon, alt, date].
        The place in the order of the coordinates as integer.
    '''
    point = geojson.Point([float(coordinate[1]), float(coordinate[0])])
    properties = {
                 "title": coordinate[3],
                 "marker-color": "#3bb2d0",
                 "marker-symbol": order
    }
    feature = geojson.Feature(geometry = point, properties = properties)
    return feature


def get_all_features():
    # First up, get all the coordinates
    coordinates = get_all_coordinates()
    # Loop through the coordinates and make the features
    locations = []
    for coordinate in coordinates:
        feature = make_feature(coordinate, len(locations) + 1)
        locations.append(feature)
    return locations
