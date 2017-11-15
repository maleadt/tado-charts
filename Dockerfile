FROM python:3-slim

RUN apt-get update \
 && apt-get install -y \
        git \
        cron \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /opt/tado/requirements.txt
WORKDIR /opt/tado
RUN pip install -r requirements.txt

COPY bin /opt/tado

ADD crontab /etc/cron.d/tado
RUN chmod 0644 /etc/cron.d/tado

VOLUME ["/output"]

ADD cron.sh /root/cron.sh
CMD ["/root/cron.sh"]
