To run this app pull the latest image of my app from package and docker:

since it a gui. Use the following commands:

install : (arch based) sudo pacman -S xorg-xhost
        : (debian based) sudo apt install xorg-xhost

1.xhost +local:docker

The .env file wil be provided in the report.
2.docker run -it --rm --env-file .env -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix imagename or id
