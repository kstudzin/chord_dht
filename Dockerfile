FROM ubuntu:latest

RUN apt install python3 python3-pip \
    && pip install pyzmq \
    && mkdir /opt/chord

COPY chord/nody.py /opt/chord/
COPY chord/util.py /opt/chord/
COPY chord/hash.py /opt/chord/