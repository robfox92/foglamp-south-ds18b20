# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

""" Plugin for a DHT11 temperature and humidity sensor attached directly to the GPIO pins of a Raspberry Pi. """

from datetime import datetime, timezone
import copy
import uuid
import logging
import glob
import os

# TODO: https://github.com/adafruit/Adafruit_Python_DHT/issues/99
import Adafruit_DHT

from foglamp.common import logger
from foglamp.services.south import exceptions


__author__ = "Mark Riddoch"
__copyright__ = "Copyright (c) 2017 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_DEFAULT_CONFIG = {
    'plugin': {
         'description': 'Python module name of the plugin to load',
         'type': 'string',
         'default': 'ds18b20'
    },
    'pollInterval': {
        'description': 'The interval between poll calls to the sensor poll routine expressed in milliseconds.',
        'type': 'integer',
        'default': '1000'
    },
}

_LOGGER = logger.setup(__name__)
""" Setup the access to the logging system of FogLAMP """
_LOGGER.setLevel(logging.INFO)


def plugin_info():
    """ Returns information about the plugin.
    Args:
    Returns:
        dict: plugin information
    Raises:
    """

    return {
        'name': 'ds18b20 GPIO',
        'version': '1.0',
        'mode': 'poll',
        'type': 'south',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG
    }


def plugin_init(config):
    """ Initialise the plugin.
    Args:
        config: JSON configuration document for the plugin configuration category
    Returns:
        handle: JSON object to be used in future calls to the plugin
    Raises:
    """

    handle = config
    return handle

def readFromSensor(sensorID):
    """ Parses the file associated with a given sensor ID

    Args:
      sensorID: the GUID of the sensor
    Returns:
      value: read value from sensor
    Raises:
      ValueError: If there is no temperature found in file or if the file fails the CRC check
    """
    sensorFilePath = "/sys/bus/w1/devices/"+sensorID+"/w1_slave"
    value = ""
    with open(sensorFilePath,'r') as sensorFile:
        sensorLines = sensorFile.readlines()

    # Check to see if the CRC check passes, otherwise raise error
    # only supports temperature based w1_slave returning values in 1000ths of 1 degree C
    if sensorLines[0].endswith("YES"):
        tempStart = sensorLines[1].find("t=")
        if tempStart != -1:
            temp = sensorLines[1][tempStart+2:]
            value = float(temp)/1000
        else:
            err = "Temperature not found in file" + sensorFilePath
            raise ValueError(err)
    else:
        err = "File fails CRC Check" + sensorFilePath
        raise ValueError(err)

    return value

def plugin_poll(handle):
    """ Extracts data from the sensor and returns it in a JSON document as a Python dict.
    Available for poll mode only.
    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
        returns a sensor reading in a JSON document, as a Python dict, if it is available
        None - If no reading is available
    Raises:
        DataRetrievalError
    """

    try:
        sensorList = []
        for sns in glob.glob('/sys/bus/w1/devices/'+'28*'):
            sensorList.append(sns.split('/')[-1])
        time_stamp = str(datetime.now(tz=timezone.utc))
        readings = {sensor: readFromSensor(sensor) for sensor in sensorList}
        wrapper = {
                    'asset':     'ds18b20',
                    'timestamp': time_stamp,
                    'key':       str(uuid.uuid4()),
                    'readings':  readings
        }
    
    except Exception:
        raise
    else:
        return wrapper


def plugin_reconfigure(handle, new_config):
    """ Reconfigures the plugin, it should be called when the configuration of the plugin is changed during the
        operation of the south service.
        The new configuration category should be passed.
    Args:
        handle: handle returned by the plugin initialisation call
        new_config: JSON object representing the new configuration category for the category
    Returns:
        new_handle: new handle to be used in the future calls
    Raises:
    """
    _LOGGER.info("Old config for DHT11 plugin {} \n new config {}".format(handle, new_config))

    new_handle = copy.deepcopy(handle)
    new_handle['restart'] = 'no'

    return new_handle


def plugin_shutdown(handle):
    """ Shutdowns the plugin doing required cleanup, to be called prior to the service being shut down.
    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
    Raises:
    """
    pass