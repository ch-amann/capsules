FROM archlinux:latest

ARG USER_ID
ARG GROUP_ID

RUN pacman -Syy
RUN pacman --noconfirm -S sudo which xorg xpra

RUN groupadd -g $GROUP_ID user
RUN useradd -m -s /bin/bash --uid $USER_ID --gid $GROUP_ID user
RUN echo "user ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/user
RUN chmod 0440 /etc/sudoers.d/user

# Create a script that copies directories from "/" to /mnt/root_dirs (make sure this is a mounted directory!)
RUN printf '#!/bin/bash\n\
DEST_DIR="/mnt/root_dirs"\n\
# Check if /mnt/root_dirs exists, if not, exit\n\
if [ ! -d "$DEST_DIR" ]; then\n\
    echo "Error: $DEST_DIR does not exist. Exiting."\n\
    exit 1\n\
fi\n\
# List of directories to exclude\n\
EXCLUDE_DIRS=("/tmp" "/proc" "/dev" "/mnt" "/sys" "/boot")\n\
\n\
# Function to check if a directory is in the exclude list\n\
exclude_dir() {\n\
    for excl in "${EXCLUDE_DIRS[@]}"; do\n\
        if [ "$1" == "$excl" ]; then\n\
            return 0  # Exclude the directory\n\
        fi\n\
    done\n\
    return 1  # Not in the exclude list\n\
}\n\
\n\
# Find top-level directories and copy them to $DEST_DIR\n\
find / -maxdepth 1 -type d ! -name ".*" ! -path "/" ! -type l | while read dir; do\n\
    if exclude_dir "$dir"; then\n\
        continue\n\
    fi\n\
    dir_name=$(basename "$dir")\n\
    echo "Copying $dir to $DEST_DIR/$dir_name"\n\
    cp -rp "$dir" "$DEST_DIR/$dir_name"\n\
done\n\
echo "Directory copy completed."\n' > /usr/local/bin/copy_root_directories.sh && chmod +x /usr/local/bin/copy_root_directories.sh

USER user
WORKDIR /home/user
