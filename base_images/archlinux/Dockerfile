FROM docker.io/archlinux:latest

ARG USER_ID
ARG GROUP_ID

RUN pacman -Syy
RUN pacman --noconfirm -S sudo which xorg xpra

RUN groupadd -g $GROUP_ID user
RUN useradd -m -s /bin/bash --uid $USER_ID --gid $GROUP_ID user
RUN echo "user ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user
RUN chmod 0440 /etc/sudoers.d/user

COPY ./setup_script.sh /usr/local/bin/copy_root_directories.sh
RUN chmod +x /usr/local/bin/copy_root_directories.sh

USER user
WORKDIR /home/user
