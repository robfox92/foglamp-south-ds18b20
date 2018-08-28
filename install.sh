#/bin/bash
# id 79adc6f1-8757-4d12-b24d-0a8fe121f97c
sudo rm -r /usr/local/foglamp/python/foglamp/plugins/south/ds18b20

sudo mkdir /usr/local/foglamp/python/foglamp/plugins/south/ds18b20
sudo cp *.py /usr/local/foglamp/python/foglamp/plugins/south/ds18b20

curl -sX POST http://localhost:8081/foglamp/service -d '{"name": "ds18b20", "type": "south", "plugin": "ds18b20", "enabled": true}'
echo "\n"
