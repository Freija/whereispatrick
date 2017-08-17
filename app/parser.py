'''
Freija <freija@gmail.com>, 2017
Utilities for:
    - parsing text message from Iridium phone to grab GPS information
    - reading in information from the local files that contain datapoints for
      GPS and photo
'''

from datetime import datetime
import re
import csv
import ast


def nospace(input_string):
    ''' return the given string with all spaces removed '''
    return input_string.replace(" ", "")


def deg_min_sec_todeg(deg, minute, sec):
    ''' This function will return degrees from degrees, minutes, seconds.
    Arguments:
        Three strings: degrees, minutes, seconds of location
    '''
    # Keep track if we have negative degrees
    is_neg = deg.startswith('-')
    degrees = abs(int(nospace(deg))) + int(minute)/60.0 + int(sec)/3600.0
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
                               r'\(.+?\)\s'
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
        result.append(datetime.strptime(matches.group(8), '%d-%b-%Y %H:%M:%S'))
        return result
    else:
        return 0


def get_all_coordinates():
    ''' This function will retrieve the coordinates from the local csv file.
    Arguments:
        None
    '''
    result = []
    with open('/data/coordinates.csv', 'r') as infile:
        reader = csv.reader(infile)
        for row in reader:
            result.append(row)
    return result


def get_all_images():
    ''' This function will retrieve the image details from the local csv file.
    Arguments:
        None
    '''
    result = []
    with open('/data/images.csv', 'r') as infile:
        reader = csv.reader(infile)
        for row in reader:
            result.append(row)
    return result


def get_all_clusters():
    ''' This function will retrieve the image details from the local csv file.
    Arguments:
        None
    '''
    result = []
    with open('/data/image_clusters.csv', 'r') as infile:
        reader = csv.reader(infile)
        for row in reader:
            this_row = []
            for item in row:
                this_row.append(ast.literal_eval(item))
            result.append(this_row)
    return result
