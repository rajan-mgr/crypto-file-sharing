To run this app fo to  the image from latest package and pull with docker.
Since it a gui based app we need to run one command before running it.

1. Install xorg-xhost:
   Most pc already came installed with it u can jump to second option.
   (archbased)
   ```bash   sudo pacman -S xorg-xhost```
  (debian based)
  ``` bash sudo apt install xorg-xhost```

2.```bash xhost +local:docker ```

The .env file will be provided in the document.
3. ```bash docker run -it --rm --env-file .env -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix imagename or id"```
