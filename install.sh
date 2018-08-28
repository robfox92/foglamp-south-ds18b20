#/bin/bash

sudo rm -r /usr/local/foglamp/python/foglamp/plugins/south/ds18b20

sudo mkdir /usr/local/foglamp/python/foglamp/plugins/south/ds18b20
sudo cp ds18b20.py /usr/local/foglamp/python/foglamp/plugins/south/ds18b20
sudo cp __init__.py /usr/local/foglamp/python/foglamp/plugins/south/ds18b20

curl -sX POST http://localhost:8081/foglamp/service -d '{"name": "ds18b20", "type": "south", "plugin": "ds18b20", "enabled": true}'

