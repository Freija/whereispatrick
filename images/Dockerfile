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

RUN echo "http://dl-8.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories
RUN apk --no-cache --update-cache add gcc gfortran python python-dev py-pip build-base wget freetype-dev libpng-dev openblas-dev
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h
RUN pip install numpy scipy pandas scikit-learn
COPY requirements.txt /
RUN pip install -r /requirements.txt

WORKDIR /images
COPY images.py client_secret.json ./
COPY credentials ./credentials
ENTRYPOINT ["python", "images.py"]
