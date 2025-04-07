FROM alpine:latest

ARG USER_ID
ARG GROUP_ID

RUN apk update
RUN apk add --no-cache sudo which xpra bash

RUN addgroup -g $GROUP_ID user
RUN adduser -h /home/user -s /bin/bash -u $USER_ID -G user -D user
RUN echo "user ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user
RUN chmod 0440 /etc/sudoers.d/user

USER user
WORKDIR /home/user
