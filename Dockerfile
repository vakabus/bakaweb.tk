FROM alpine:3.8

EXPOSE 80

# install python3 and pip
RUN apk add --no-cache python3 python3-dev && \
 python3 -m ensurepip && \
 rm -r /usr/lib/python*/ensurepip && \
 pip3 install --upgrade pip setuptools && \
 if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
 if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
 rm -r /root/.cache

# install universal dependencies
RUN apk add --no-cache gcc g++ make libffi-dev openssl-dev git redis
RUN pip install django bleach PyCrypto xmltodict requests gunicorn gevent redis git+https://github.com/Supervisor/supervisor.git
RUN apk del gcc g++ make

# install pybakalib
RUN pip install git+https://github.com/vakabus/pybakalib.git

# copy data to container
RUN mkdir /code
RUN mkdir /data
RUN mkdir /data/log

COPY . /code

# create log directory
RUN mkdir /log

# run
WORKDIR /code
CMD supervisord -c supervisord.conf
