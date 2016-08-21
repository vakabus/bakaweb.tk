#! /bin/bash

sudo systemctl stop schooltools.service
cd "/home/schooltools/pyschooltools"
git pull
sudo pip3 install --upgrade https://github.com/vakabus/pybakalib/archive/master.zip
sudo systemctl start schooltools.service