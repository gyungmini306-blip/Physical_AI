FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates python3 git && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=/usr/local/bin sh
ENV ARDUINO_BOARD_MANAGER_ADDITIONAL_URLS="https://espressif.github.io/arduino-esp32/package_esp32_index.json"
RUN arduino-cli core update-index && arduino-cli core install esp32:esp32@3.3.12
WORKDIR /workspace
CMD ["bash"]
