#!/bin/bash

# make sure we are in the correct path
cd /code/pyschooltools

# update code
git pull origin master

# rebuild
docker build -t bakaweb .

# redeploy
docker stop bakaweb-container
docker rm bakaweb-container
docker run -d -p 8000:80 -v /var/bakaweb:/data --restart=always --name=bakaweb-container bakaweb:latest
