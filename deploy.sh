#! /bin/bash

sudo systemctl stop schooltools.service
sudo systemctl stop schooltools_check.service
sudo systemctl stop schooltools_check.timer
cd "/home/schooltools/pyschooltools"
git pull
python3 manage.py migrate
chmod 0660 db.sqlite3
sudo pip3 install --upgrade https://github.com/vakabus/pybakalib/archive/master.zip
sudo pip3 install -r requirements.txt
sudo systemctl start schooltools.service
sudo systemctl start schooltools_check.timer