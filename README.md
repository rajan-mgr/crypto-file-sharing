To run this from docker:
since it a gui. Use the following commands:

install : (arch based) sudo pacman -S xorg-xhost
        : (debian based) sudo apt install xorg-xhost

1.xhost +local:docker

2.docker run -it --rm --env-file .env -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix <image-name or id>
