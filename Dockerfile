FROM python:alpine3.8

EXPOSE 80

# install universal dependencies
RUN apk add --no-cache gcc g++ make libffi-dev openssl-dev git redis
RUN pip install pipenv gunicorn gevent redis git+https://github.com/Supervisor/supervisor.git

# prepare directory structure...
RUN mkdir /code
RUN mkdir /data
RUN mkdir /data/log
RUN mkdir /log

WORKDIR /code

# install dependencies for the webserver
COPY Pipfile /code/
COPY Pipfile.lock /code/
RUN pipenv install --system --deploy --ignore-pipfile

# Install server
COPY . /code

CMD supervisord -c supervisord.conf
