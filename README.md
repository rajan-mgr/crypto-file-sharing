```bash
# Install dependencies
# Arch-based
sudo pacman -S xorg-xhost

# Debian-based
sudo apt install xorg-xhost

# Step 1: Allow local Docker access to X server
xhost +local:docker

# The .env file will be provided in the report.

# Step 2: Run Docker container
docker run -it --rm --env-file .env -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix imagename_or_id
