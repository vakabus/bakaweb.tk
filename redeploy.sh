#!/bin/bash

docker build -t bakaweb .
docker stop bakaweb-container
docker run --rm -p 8000:80 -v /var/bakaweb:/data --restart=always --name=bakaweb-container bakaweb:latest
