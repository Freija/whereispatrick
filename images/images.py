'''Grabbing photos from Google Drive
# Freija <freija@gmail.com>'''

from __future__ import print_function
import os
import glob
import io
import csv
import shutil
from datetime import datetime
from time import sleep

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
# at ~/.credentials/drive-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'whereispatrick'


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
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
    ''' This function will retrieve the meta information
    of the images from the local csv file.
    Arguments:
        None
    '''
    result = []
    with open('/data/images.csv', 'r') as infile:
        reader = csv.reader(infile)
        for row in reader:
            result.append(row)
    return result


def get_sign(code):
    ''' This function will return the sign corresponding to the supplied
    code. Input is 'E', 'W', 'N' or 'S'.
    '''
    if code == 'W' or code == 'S':
        return -1
    elif code == 'E' or code == 'N':
        return 1
    else:
        # wrong location code
        return 0


def deg_min_sec_todeg(degs, mins, secs, sign_code):
    ''' This function will return degrees from degrees, minutes, seconds.
    Arguments:
        Three tuples: (degrees, denom), (min, denom), (sec, denom) of location
        One string: sign_code can be W, E, S or N
    '''
    # Keep track if we have negative degrees
    sign = get_sign(sign_code)
    if sign == 0:
        return 0
    else:
        degrees = degs[0] / (degs[1]*1.0) + \
                  mins[0] / (mins[1]*60.0) + \
                  secs[0] / (secs[1]*3600.00)
        return sign * degrees


def get_image_gps_info(image):
    '''The piece of info we want is in the GPS section of the exif. This can
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
            return 0, image, 0, 0, 0, 0  # Something went wrong
        # Also get the altitude
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
        # downloads.
        return 0, image, 0, 0, 0, 0


def list_files(service):
    ''' Generator to yield the GD files.
    From https://gist.github.com/revolunet/9507070
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
    ''' Helper function that return a square png thumbnail of the provided
    jpg image and dimension.
    '''
    size = (dimension, dimension)
    image = Image.open(image_name)
    image.thumbnail(size, Image.ANTIALIAS)
    background = Image.new('RGBA', size, (255, 255, 255, 0))
    background.paste(image, (int((size[0] - image.size[0]) / 2),
                             int((size[1] - image.size[1]) / 2)))
    new_image = image_name.replace('.jpg', '.png')
    background.save(new_image)
    return new_image


def process_all_jpgs():
    ''' Helper function to deal with the older full-sized jpgs. They will all
    be made into smaller png thumbnails and removed.
    '''
    # All we have to do is make a list of the jpg files in the image directory
    # and process them. FIXME (Freija) implement this!
    for infile in glob.glob("/data/images/*.jpg"):
        print(infile)
        jpg_to_png_thumbnail(500, infile)
        # Remove the full sized jpg to save space
        os.remove(infile)


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


def get_pictures():
    ''' Get the latest images from the Google Drive. Inspired by the
    Google Drive example code:
    (https://developers.google.com/drive/v3/web/quickstart/python).
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
                continue
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
            # We have a new image, save the information to the CSV file
            image_info = get_image_gps_info(item['name'])
            # Add the coordinates to our local coordinates file
            with open(r'/data/images.csv', 'a') as outf:
                writer = csv.writer(outf)
                writer.writerow(image_info)
            # Process the image
            process_image(item['name'])


def main():
    ''' Check for new pictures on the Google Drive every hour.
    '''
    while True:
        # First, check if there are any full-sized jpgs in the image directory.
        # If so, make the png thumbnails and remove the full-sized images.
        process_all_jpgs()
        # Check the Google Drive for available pictures.
        # If so, download, grab GPS info and make the thumbnail.
        get_pictures()
        # Wait one hour to check again.
        sleep(3600)


if __name__ == '__main__':
    main()
