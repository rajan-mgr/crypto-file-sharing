To run this from docker:
since it a gui. Use the following commands:
1.xhost +local:docker

2.sudo docker run -it \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  rm/secureshare
