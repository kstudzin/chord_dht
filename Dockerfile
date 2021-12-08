FROM ubuntu:latest

RUN apt-get update \
    && apt install -y python3 python3-pip \
    && pip install pyzmq \
    && mkdir /opt/chord

COPY chord/node.py /opt/chord/
COPY chord/util.py /opt/chord/
COPY chord/hash.py /opt/chord/
