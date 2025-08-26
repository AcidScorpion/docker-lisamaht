# Use Debian old-stable as the base image
FROM debian:bookworm

COPY requirements.txt /opt/

SHELL ["/bin/bash", "-c"]

# Install Python, playwright, requests
# Setup chromium-headless-shell and its dependencies
RUN apt update && apt install -y \
    python3 \
    python3-venv \
    && python3 -m venv /opt/.venv \
    && source /opt/.venv/bin/activate \
    && pip3 install --upgrade pip \
    && pip3 install -r /opt/requirements.txt \
    && playwright install chromium-headless-shell \
    && playwright install-deps

# Set the working directory
WORKDIR /opt

# Set the entrypoint command
ENTRYPOINT [ "/opt/.venv/bin/python3", "/opt/lisamaht.py" ]