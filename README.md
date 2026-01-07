To run this from docker:
since it a gui. Use the following commands:
1.xhost +local:docker

2.docker run -it --rm \                                                            
--env-file .env \
-e DISPLAY=$DISPLAY \
-v /tmp/.X11-unix:/tmp/.X11-unix \
ghcr.io/rajan-mgr/secureshare:v1.0.3
