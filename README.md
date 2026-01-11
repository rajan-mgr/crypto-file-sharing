# Docker GUI Application Setup

This guide explains how to run this GUI-based application using Docker.

## Prerequisites

- Docker installed on your system
- X11 server (for GUI display)
- `.env` file with required environment variables

## Installation Steps

### 1. Install xorg-xhost

Most systems come with `xorg-xhost` pre-installed. If not, install it using your package manager:

**Arch-based distributions:**
```bash
sudo pacman -S xorg-xhost
```

**Debian-based distributions:**
```bash
sudo apt install xorg-xhost
```

### 2. Configure X11 Access

Allow Docker containers to access your X11 display:
```bash
xhost +local:docker
```

> **Note:** This command needs to be run once per session (after each system restart).

### 3. Pull the Docker Image

Pull the latest version of the application:
```bash
docker pull <image-name>
```

Replace `<image-name>` with the actual image name from the package repository.

### 4. Run the Application
The .env file will be provided in the document.
Run the container with the following command:
```bash
docker run -it --rm \
  --env-file .env \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  <image-name-or-id>
```

**Command breakdown:**
- `-it` - Interactive mode with terminal
- `--rm` - Automatically remove container after exit
- `--env-file .env` - Load environment variables from `.env` file
- `-e DISPLAY=$DISPLAY` - Pass display environment variable
- `-v /tmp/.X11-unix:/tmp/.X11-unix` - Mount X11 socket
- `<image-name-or-id>` - Replace with your image name or ID

## Environment Configuration

Ensure your `.env` file is present in the same directory before running the container. The required environment variables will be documented separately.

## Troubleshooting

### GUI not displaying
- Verify X11 forwarding is enabled: `echo $DISPLAY`
- Re-run: `xhost +local:docker`
- Check if X11 socket exists: `ls /tmp/.X11-unix`

### Permission issues
- Ensure Docker has necessary permissions
- Try running with `sudo` if needed (not recommended for regular use)

## Security Note

The `xhost +local:docker` command allows local Docker containers to access your X server. For improved security, consider using more restrictive xhost configurations in production environments.
