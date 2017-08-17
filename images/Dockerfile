FROM ubuntu

# we need this to install bpython for test
RUN apt-get update

#Install python basics
RUN apt-get -y install \
	build-essential \
	python-dev \
	python-setuptools \
	python-pip


#Install scikit-learn dependancies
RUN apt-get -y install \
          python-numpy \
          python-scipy \
          python-pandas \
          libatlas-dev \
          libatlas3-base

#Install scikit-learn
RUN apt-get -y install python-sklearn
RUN pip install --upgrade pip
COPY requirements.txt /
RUN pip install -r /requirements.txt

WORKDIR /images
COPY images.py client_secret.json ./
COPY credentials ./credentials
ENTRYPOINT ["python", "images.py"]
