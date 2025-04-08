FROM debian:12

ARG USER_ID
ARG GROUP_ID

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y sudo dbus-x11 wget curl gnupg2 lsb-release ca-certificates

# Add the GPG key for the xpra repository
RUN wget -qO - https://xpra.org/gpg.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/xpra-archive.gpg

# Add the XPRA noble repository to the sources list
RUN echo "deb https://xpra.org/ bookworm main" > /etc/apt/sources.list.d/xpra-noble.list

RUN apt-get update
RUN apt-get install -y xpra

RUN groupadd -g $GROUP_ID user
RUN useradd -m -s /bin/bash --uid $USER_ID --gid $GROUP_ID user
RUN echo "user ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user
RUN chmod 0440 /etc/sudoers.d/user

COPY ./setup_script.sh /usr/local/bin/copy_root_directories.sh
RUN chmod +x /usr/local/bin/copy_root_directories.sh

USER user
WORKDIR /home/user

