# whereispatrick
Website to locate Patrick.

## Introduction
### The challenge
My father is currently travelling from Quito, Equador to Ushuaia, Argentina... by bike.
A trip of a lifetime that will take him 9-12 months. He brought a satellite phone with him, which he uses to regularly send
coordinates by sms to a group of cellphone numbers. I wanted to make a website (whereispatrick.at, password protected) that
shows all the coordinates on a single map. In addition, he also takes geo-tagged photos, which are uploaded to Google Photos.
The locations of the photos and thumbnails of the photos make a nice addition to the map.

### The solution
This project consists of a Flask API and website:
  * The satellite sms are forwarded to the API using Twilio. The coordinates are extracted and stored in a local CSV file.
  * The photos are retrieved through the Google Drive API. The coordinates are extracted and stored in a local CSV file. The photos are converted to smaller thumbnails.
  * The coordinates are mapped on a Google Map using the Google Maps API. When clicking on a satellite-phone point, an info
  window pops up to show the date and altitude. When clicking on a photo point, the info window also contains the thumbnail of the
  photo.

