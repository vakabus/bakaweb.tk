#! /bin/bash

sudo systemctl stop schooltools.service
cd "/home/schooltools/pyschooltools"
git pull
python3 manage.py migrate
chmod 0660 db.sqlite3
sudo pip3 install --upgrade https://github.com/vakabus/pybakalib/archive/master.zip
sudo systemctl start schooltools.service