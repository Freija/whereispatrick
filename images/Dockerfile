FROM python:2.7-alpine

# we need this to install bpython for test
RUN apk add --no-cache build-base

COPY requirements.txt /
RUN pip install -r /requirements.txt

WORKDIR /images
COPY images.py client_secret.json ./
COPY credentials ./credentials
ENTRYPOINT ["python", "images.py"]
