FROM debian:jessie

RUN apt-get update && apt-get upgrade -y

# install dependencies
RUN apt-get install -y python3 python3-flask python3-crypto python3-flask-sqlalchemy \
                       nginx \
                       curl wget netcat

ADD src /var/www/src

# configure website
WORKDIR /var/www/src

RUN python3 -c "import sys, os; sys.stdout.buffer.write(os.urandom(16))" > private-key && \
    python3 initdb.py && \
    mv flag.txt /flag

WORKDIR /etc/nginx

# configure nginx
RUN echo -e "\ndaemon off;" >> nginx.conf
# TODO: configure nginx + uwsgi

EXPOSE 5000

WORKDIR /var/www/src
CMD python3 app.py
