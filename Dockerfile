FROM debian:jessie

# full upgrade
RUN apt-get update && apt-get upgrade -y

# install dependencies
RUN apt-get install -y python3 python3-flask python3-crypto python3-flask-sqlalchemy \
                       uwsgi uwsgi-plugin-python3 \
                       nginx supervisor \
                       curl wget netcat

ADD src /var/www/src

# configure website
WORKDIR /var/www/src

RUN find . -type f -exec chmod 644 '{}' \; && \
    find . -type d -exec chmod 755 '{}' \; && \
    python3 -c "import sys, os; sys.stdout.buffer.write(os.urandom(16))" > private-key && \
    chmod 644 private-key && \
    python3 initdb.py && \
    chown www-data:www-data /tmp/database.db && chmod 660 /tmp/database.db && \
    mv flag.txt /flag

# configure nginx
WORKDIR /etc/nginx

RUN echo "daemon off;" >> nginx.conf && \
    rm sites-enabled/default && \
    mv /var/www/src/nginx.conf sites-enabled/default

# configure supervisord
WORKDIR /etc/supervisor

RUN mv /var/www/src/supervisord.conf conf.d/supervisord.conf

EXPOSE 80

CMD ["supervisord"]
