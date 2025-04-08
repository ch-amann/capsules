FROM docker.io/ubuntu:noble

ARG USER_ID
ARG GROUP_ID

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y sudo dbus-x11 wget curl gnupg2 lsb-release ca-certificates

# Add the GPG key for the xpra repository
RUN wget -qO - https://xpra.org/gpg.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/xpra-archive.gpg

# Add the XPRA noble repository to the sources list
RUN echo "deb https://xpra.org/ noble main" > /etc/apt/sources.list.d/xpra-noble.list

RUN apt-get update
RUN apt-get install -y xpra

COPY ./setup_script.sh /usr/local/bin/copy_root_directories.sh
RUN chmod +x /usr/local/bin/copy_root_directories.sh

# User and group with uid/gid 1000 exist already.
# They are both called 'ubuntu' which is fine.
# Could be renamed with the next two commands:

# RUN usermod -l user -d /home/user -m ubuntu
# RUN groupmod -n user ubuntu

# RUN echo "user ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user
# RUN chmod 0440 /etc/sudoers.d/user

# USER user
# WORKDIR /home/user


RUN echo "ubuntu ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/ubuntu
RUN chmod 0440 /etc/sudoers.d/ubuntu

USER ubuntu
WORKDIR /home/ubuntu
