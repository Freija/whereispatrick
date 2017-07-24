FROM python:2.7-alpine

# we need this to install bpython for test
RUN apk add --no-cache build-base
# these are the pillow dependencies
RUN apk add --no-cache zlib-dev  \
                       jpeg-dev \
                       freetype-dev \
                       lcms2-dev \
                       openjpeg-dev \
                       tiff-dev \
                       tk-dev \
                       tcl-dev \
                       harfbuzz-dev \
                       fribidi-dev

COPY requirements.txt /
RUN pip install -r /requirements.txt

WORKDIR /images
COPY images.py client_secret.json ./
COPY credentials ./credentials
ENTRYPOINT ["python", "images.py"]
