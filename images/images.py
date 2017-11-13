'''
Freija <freija@gmail.com>, 2017
Utilities for:
    - grabbing photos from Google Drive
    - retrieving their coordinates from the EXIF info
    - making thumbnails
    - finding clusters in the coordinates and group photos by cluster
'''

from __future__ import print_function
import os
import glob
import io
import csv
import shutil
import math
from datetime import datetime
from time import sleep

# External imports
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from PIL import Image
import httplib2
import piexif
from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

# The following is needed to handle the possible command line arguments,
# for example when updating the credentials.
try:
    import argparse
    CLFLAGS = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    CLFLAGS = None

# If modifying these scopes, delete your previously saved credentials
# so that new credentials can be created.
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'whereispatrick'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials. Note that
    you will need to specify the command-line option since the browser will
    not be launched from the Docker.
    Arguments:
        None
    Returns:
        credentials: the obtained credential.
    """
    home_dir = os.path.expanduser('.')
    credential_dir = os.path.join(home_dir, 'credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'whereispatrickcred.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if CLFLAGS:
            credentials = tools.run_flow(flow, store, CLFLAGS)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def get_images_list():
    ''' Retrieves the meta information of the images from the local CSV file.

    Arguments:
        None
    Returns:
        list: a list of the image information for all lines in the image file.
    '''
    result = []
    with open('/data/images.csv', 'r') as infile:
        reader = csv.reader(infile)
        for row in reader:
            result.append(row)
    return result


def get_sign(code):
    ''' Returns the sign corresponding to the supplied code.

    Arguments:
        One of the following strings: 'E', 'W', 'N' or 'S' for Eastern,
        Western, Northern or Southern hemisphere.
    Returns:
        int: -1 for W and S, 1 for E and N, 0 for all other situations.
    '''
    if code == 'W' or code == 'S':
        return -1
    elif code == 'E' or code == 'N':
        return 1
    else:
        # Wrong location code.
        return 0


def deg_min_sec_todeg(degs, mins, secs, sign_code):
    ''' Returns degrees from degrees, minutes, seconds.

    Arguments:
        tuples: (degrees, denom), (min, denom), (sec, denom) of location.
        string: sign_code can be W, E, S or N.
    Returns:
        float: the degrees corresponding to these coordinates.
    '''
    # Keep track if we have negative degrees.
    sign = get_sign(sign_code)
    if sign == 0:
        return 0
    else:
        degrees = degs[0] / (degs[1]*1.0) + \
                  mins[0] / (mins[1]*60.0) + \
                  secs[0] / (secs[1]*3600.00)
        return sign * degrees


def get_image_gps_info(image):
    ''' Returns the GPS information found in the EXIF of the image.

    The piece of info we want is in the GPS section of the EXIF. This can
    be different for different camera models.
    In my case, this is the format of that info (example numbers):
       {
        0: (2, 2, 0, 0),                          GPS tag version
        1: 'S',                                   North or South latitude
        2: ((11, 1), (52, 1), (261135, 10000)),   latitude
        3: 'W',                                   East or West longitude
        4: ((75, 1), (17, 1), (398785, 10000)),   longitude
        5: 0,                                     altidude reference level
        6: (3422, 1),                             altitude
        7: ((15, 1), (29, 1), (10, 1)),           time
        27: some crazy stuff,                     undefined data (?)
        29: '2017:07:12'                          date
        }
    Arguments:
        string: name of the image for which to extract the EXIF information.
    Returns:
        int: 1 (use this image) or 0 (do not use this image).
        string: name of the image.
        float: latitude in degrees.
        float: longitude in degrees.
        float: altitude in unit of the phone setting.
        datetime: date_and_time in the phone setting (not always local time).
    '''
    exif = piexif.load(image)
    # Make sure that there is in fact GPS information available.
    if len(exif['GPS']) > 0:
        # First get the coordinates in the correct Google Maps API shape.
        # Google maps API wants the coordinates in degrees, with the sign
        # indicating the hemispheres.
        # See key in docstring above.
        latitude = deg_min_sec_todeg(exif['GPS'][2][0],   # degrees
                                     exif['GPS'][2][1],   # minutes
                                     exif['GPS'][2][2],   # seconds
                                     exif['GPS'][1])      # hemisphere
        longitude = deg_min_sec_todeg(exif['GPS'][4][0],  # degrees
                                      exif['GPS'][4][1],  # minutes
                                      exif['GPS'][4][2],  # seconds
                                      exif['GPS'][3])     # hemisphere
        if latitude == 0 or longitude == 0:
            return 0, image, 0, 0, 0, 0  # Something went wrong.
        # Also get the altitude.
        altitude = exif['GPS'][6][0]/exif['GPS'][6][1]
        # Now get the time and put in datetime format.
        # You probably want to check the time zone. For these
        # pictures, the GPS time is not in local time.
        hour = exif['GPS'][7][0][0]/exif['GPS'][7][0][1]
        minute = exif['GPS'][7][1][0]/exif['GPS'][7][1][1]
        second = exif['GPS'][7][2][0]/exif['GPS'][7][2][1]
        datestring = '{0} {1}:{2}:{3}'.format(exif['GPS'][29], hour,
                                              minute, second)
        date_and_time = datetime.strptime(datestring, '%Y:%m:%d %H:%M:%S')
        return 1, image, latitude, longitude, altitude, date_and_time
    else:
        # No GPS coordinates available. We still want an entry to indicate
        # that this picture was processed. This will prevent duplicate GD
        # downloads. The first 0 indicates that this photo should not be
        # displayed on the map.
        return 0, image, 0, 0, 0, 0


def list_files(service):
    ''' Generator to yield the GD files.
    From https://gist.github.com/revolunet/9507070
    Arguments:
        service: the GD API service handler.
    Yields:
        dict:
    '''
    page_token = None
    while True:
        param = {}
        if page_token:
            param['pageToken'] = page_token
        files = service.files().list(**param).execute()
        for item in files['files']:
            yield item
        page_token = files.get('nextPageToken')
        if not page_token:
            break


def jpg_to_png_thumbnail(dimension, image_name):
    ''' Creates and saves a png thumbnail of the provided
    jpg image and width dimension.

    Arguments:
        int:width dimension of thumbnail in pixels.
        string: name of the image.
    Returns:
        string: name of the new image.
    '''

    image = Image.open(image_name)
    wpercent = (dimension/float(image.size[0]))
    hsize = int((float(image.size[1])*float(wpercent)))
    img = image.resize((dimension, hsize), Image.ANTIALIAS)
    new_image = image_name.replace('.jpg', '.png')
    img.save(new_image)
    return new_image


def process_all_jpgs():
    ''' Processes all local full-sized jpgs.

    All local full-sized jpgs will be made into smaller png thumbnails and
    removed. This is a way to make sure that we do not have any full-sized
    photos taking up space on the server.

    Arguments:
        None
    Returns:
        None
    '''
    # All we have to do is make a list of the jpg files in the image directory
    # and process them.
    for infile in glob.glob("/data/images/*.jpg"):
        jpg_to_png_thumbnail(500, infile)
        # Remove the full sized jpg to save space.
        os.remove(infile)


def process_all_png():
    ''' Processes all pngs.

    Crop the old PNGs.

    Arguments:
        None
    Returns:
        None
    '''
    # All we have to do is make a list of png files in the image directory
    # and process them.
    for infile in glob.glob("/data/images/*.png"):
        process_old_png(infile)


def process_image(image_name):
    ''' function to do some image manipulations
    '''
    # We only want to keep smaller sized images to show on the website.
    new_image = jpg_to_png_thumbnail(500, image_name)
    # Move the new image to the correct directory.
    shutil.move(new_image,
                "/data/images/{0}".format(new_image))
    # Remove the full sized jpg to save space
    os.remove(image_name)


def process_old_png(image_name):
    ''' Function to reprocess old png files to remove the
    whitespace.
    '''
    image = Image.open(image_name)
    image.load()
    imagesize = image.size
    if imagesize != (500, 500):
        return -1
    imagecomponents = image.split()
    rgbimage = Image.new("RGB", imagesize, (0, 0, 0))
    rgbimage.paste(image, mask=imagecomponents[3])
    croppedbox = rgbimage.getbbox()
    cropped = image.crop(croppedbox)
    # Overwrite the old image
    cropped.save(image_name)
    return 0


def get_pictures():
    ''' Gets the latest images from the Google Drive.

    Inspired by the Google Drive example code:
    (https://developers.google.com/drive/v3/web/quickstart/python).
    Arguments:
        None
    Returns:
        None
    '''
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)
    # Grab the current list of images
    local_images = get_images_list()
    # Make a set of the image names that were already processed.
    local_image_names_set = set([image_info[1] for image_info in local_images])
    for item in list_files(service):
        # Only process jpg files. If there are multiple directories, you can
        # check the file parents to make sure you are looking in the right
        # directory. Not needed in my case.
        if item['name'].endswith('.jpg'):
            # Is this an image we need to download?
            if item['name'] in local_image_names_set:
                continue  # No, skip it.
            # New picture! Time to download and process.
            print('{0} --> {1} ({2})'.format(datetime.now(),
                                             item['name'],
                                             item['id']))
            request = service.files().get_media(fileId=item['id'])
            filehandle = io.FileIO(item['name'], 'wb')
            downloader = MediaIoBaseDownload(filehandle, request)
            done = False
            while done is False:
                _, done = downloader.next_chunk()
            # We have a new image, save the information to the CSV file.
            image_info = get_image_gps_info(item['name'])
            # Add the coordinates to our local coordinates file.
            with open(r'/data/images.csv', 'a') as outf:
                writer = csv.writer(outf)
                writer.writerow(image_info)
            # Process the image.
            process_image(item['name'])


def get_cluster_center(cluster):
    ''' Finds center of cluster.

    Arguments:
        np.array: the coordinates in degrees of the cluster
    Returns:
        tuple: the coordinates (lat, lon) of the cluster center.
    '''
    x_coord = 0.0
    y_coord = 0.0
    z_coord = 0.0
    for lat, lon in cluster:
        lat = float(lat * math.pi/180.0)  # convert to radians
        lon = float(lon * math.pi/180.0)  # convert to radians
        x_coord += math.cos(lat) * math.cos(lon)
        y_coord += math.cos(lat) * math.sin(lon)
        z_coord += math.sin(lat)
    x_coord = float(x_coord / len(cluster))
    y_coord = float(y_coord / len(cluster))
    z_coord = float(z_coord / len(cluster))
    center_lat = math.atan2(z_coord,
                            math.sqrt(x_coord * x_coord + y_coord * y_coord))
    center_lon = math.atan2(y_coord, x_coord)
    return (center_lat * 180.0/math.pi, center_lon * 180.0/math.pi)


def clustering(cluster_radius):
    ''' Finds clusters in the coordinates of the photos.

    This will allow the bunching photos that have been taken close together.
    Inspired by the following blog post:
    http://geoffboeing.com/2014/08/clustering-to-reduce-spatial-data-set-size/
    Arguments:
        float: cluster radius in meters.
    Returns:
        None
    '''
    # Get the coordinates from the CSV file
    my_df = pd.read_csv('/data/images.csv', header=None)
    coords = my_df.as_matrix(columns=[2, 3])
    image_info = my_df.as_matrix(columns=[1, 2, 3, 4, 5])
    # Set up the DBSCAN algorithm from scikit-learn. See
    # http://scikit-learn.org/
    epsilon = cluster_radius / 6371008.8  # Denominator is m per Earth radian
    # Set the mon_samples to 1: this is the minimum number of samples per
    # cluster. In our case, one photo can be a cluster and should be displayed.
    my_dbscan = DBSCAN(eps=epsilon, min_samples=1,
                       algorithm='ball_tree',
                       metric='haversine').fit(np.radians(coords))
    # Each photo is now labeled with a cluster-number.
    cluster_labels = my_dbscan.labels_
    num_clusters = len(set(cluster_labels))
    clusters = pd.Series([coords[cluster_labels == n]
                          for n in range(num_clusters)])
    # Find the center of each cluster. This is where marker for the
    # photo cluster should be.
    images = pd.Series([image_info[cluster_labels == n]
                        for n in range(num_clusters)])
    # Time to deal with duplicate images. Duplicate images can occur from
    # testing and not cleaning up afterwards! Just brute-force for now.
    images_list = []
    for index, item in enumerate(images):
        local_image_list = []
        images_list.append([])
        for _, sub_item in enumerate(item):
            if sub_item[0] in local_image_list:
                continue
            images_list[index].append(sub_item.tolist())
            local_image_list.append(sub_item[0])
    with open(r'/data/image_clusters.csv', 'w') as outf:
        for index, cluster in enumerate(clusters):
            if index == 0:
                continue  # These are all the images without coordinates
            # index will also be the cluster number.
            center = get_cluster_center(cluster)
            cluster_info = index, list(center), images_list[index]
            writer = csv.writer(outf)
            writer.writerow(cluster_info)


def main():
    ''' Check for new pictures on the Google Drive every hour and extract the
    clustering.
    '''
    while True:
        # First, check if there are any full-sized jpgs in the image directory.
        # If so, make the png thumbnails and remove the full-sized images.
        process_all_jpgs()
        # Reprocess the old pngs, uncomment if needed
        # process_all_png()
        # Check the Google Drive for available pictures.
        # If so, download, grab GPS info and make the thumbnail.
        get_pictures()
        # Re-run the clustering for the photos
        clustering(100.0)  # The argument is the cluster radius.
        # Wait one hour to check again.
        sleep(3600)


if __name__ == '__main__':
    main()
