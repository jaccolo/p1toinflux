FROM debian:11-slim
LABEL org.opencontainers.image.authors="jacco@tetter.nl"
COPY p1toinflux.py /p1toinflux.py
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/* && pip install influxdb-client
# -u for unbuffered output to stdout/stderr to immediately show output
CMD ["/usr/bin/python3", "-u", "/p1toinflux.py"]
