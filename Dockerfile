# Download base image ubuntu 22.04
ARG tag=jammy
FROM ubuntu:${tag}

## LABEL about the custom image
MAINTAINER Daniel Garcia Diaz (IFCA) <garciad@ifca.unican.es>
LABEL version="0.1"
LABEL description="Freshwater quality monitoring by remote sensing. Sentinel-2 and Landsat 8"

## Set environment variables
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
        
# Install ubuntu updates and python related stuff
RUN apt-get update --fix-missing
RUN apt-get install -y wget \
	bzip2 \
	ca-certificates \
	build-essential \
	curl \
	git \
	git-core \
	pkg-config \
	python3-dev \
	python3-pip \
	python3-setuptools \
	python3-virtualenv \
	unzip \
	software-properties-common \
	llvm \
        ffmpeg libsm6 libxext6

## Install GDAL &  python-gdal
RUN apt install -y gdal-bin python3-gdal
RUN add-apt-repository ppa:ubuntugis/ppa
RUN apt-get update
RUN apt-get install -y gdal-bin

## Install python APIs
RUN pip3 install --upgrade pip
RUN pip3 install jupyter notebook
RUN ls -lahS
RUN git clone https://github.com/ferag/wq_sat.git
WORKDIR wq_sat
RUN python3 setup.py install


EXPOSE 8888

## Starts up the notebook
CMD ["jupyter", "notebook", "--port=8888", "--no-browser", "--ip=0.0.0.0", "--allow-root"]

