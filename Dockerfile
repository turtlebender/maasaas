FROM ubuntu:12.04
MAINTAINER Tom Howe

RUN echo 'deb-src http://gb.archive.ubuntu.com/ubuntu/ precise main' >> /etc/apt/sources.list
RUN echo 'deb http://gb.archive.ubuntu.com/ubuntu/ precise universe' >> /etc/apt/sources.list
RUN echo 'deb http://gb.archive.ubuntu.com/ubuntu/ precise multiverse' >> /etc/apt/sources.list

RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
RUN echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' | tee /etc/apt/sources.list.d/mongodb.list
RUN apt-get update
RUN apt-get install mongodb-10gen
#RUN echo "mongodb-10gen hold" | dpkg --set-selections

EXPOSE 27017
EXPOSE 27018
