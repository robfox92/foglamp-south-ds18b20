# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

"""
Poll based south plugin to retrieve data from w1-gpio devices on a raspberry pi,
based on the following template: https://github.com/foglamp/FogLAMP-Examples/blob/master/south_plugin_poll/python/foglamp/plugins/south/poll_template/poll_template.py
"""

import copy
from datetime import datetime, timezone
import random
import uuid
import re
import os
import glob


os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

from foglamp.common import logger
from foglamp.services.south import exceptions

__author__ = "Robert Fox"
__copyright__ = "Copyright (c) 2018 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_DEFAULT_CONFIG = {
    'plugin': {
         'description': 'Plugin name',
         'type': 'string',
         'default': 'ds18b20'
    },
    'pollInterval': {
        'description': 'The interval between polling calls (in milliseconds)',
        'type': 'integer',
        'default': '1000'
    }

}

_LOGGER = logger.setup(__name__)


def plugin_info():
    """ Returns information about the plugin

    Args:
    Returns:
        dict: plugin information
    Raises:
    """

    return {
        'name': 'ds18b20 Plugin',
        'version': '1.0',
        'mode': 'poll', ''
        'type': 'south',
        'interface': '1.0',
        'config': _DEFAULT_CONFIG}


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
    # Need to strip newlines, couls also alter the test
    if sensorLines[0].strip("\n").endswith("YES"):
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


def plugin_init(config):
    """ Initialise the plugin.

    Args:
        config: JSON configuration document for the South plugin configuration category
    Returns:
        handle: JSON object to be used in future calls to the plugin
    Raises:
    """
    handle = config

    # Split the IDs out to handles
    handle['sensorIDs'] = []
    handle['sensorList'] = glob.glob('/sys/bus/w1/devices/'+'28*')
    for sns in glob.glob('/sys/bus/w1/devices/'+'28*'):
        handle['sensorIDs'].append(sns.split('/')[-1])


    return handle



def plugin_poll(handle):
    """ Extracts data from the sensor and returns it in a JSON document as a Python dict.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
        returns a sensor reading in a JSON document;
        A Python dict - if it is available,
        None - If no reading is available
    Raises:
        DataRetrievalError
    """

    timestamp = str(datetime.now(tz=timezone.utc))

    # Update the sensor IDs every time the thing polls
    newglob = glob.glob('/sys/bus/w1/devices/'+'28*')
    if handle['sensorList'] != newglob:
        handle['sensorList'] = newglob
        handle['sensorIDs'] = []
        for sns in newglob:
            handle['sensorIDs'].append(sns.split('/')[-1])
    try:
        data = {
                'asset': 'ds18b20',
                'timestamp': timestamp,
                'key': str(uuid.uuid4()),
                'readings':  { sensor:readFromSensor(sensor) for sensor in handle['sensorIDs']}
        }

    except Exception as ex:
        raise exceptions.DataRetrievalError(ex)

    return data


def plugin_reconfigure(handle, new_config):
    """ Reconfigures the plugin,

    it should be called when the configuration of the plugin is changed during the operation of the South plugin service
    The new configuration category should be passed.

    Args:
        handle: handle returned by the plugin initialisation call
        new_config: JSON object representing the new configuration category
    Returns:
        new_handle: new handle to be used in the future calls
    Raises:
    """

    # Find diff between old config and new config
    diff = dict()  # get diff(handle, new_config)

    # Plugin should re-initialize and restart if key configuration is changed
    # e.g. port / uri / management_host or BLE address etc.
    if 'port' in diff or 'uri' in diff or 'management_host' in diff:
        # write necessary code to stop the plugin here
        new_handle = plugin_init(new_config)
        new_handle['restart'] = 'yes'
        _LOGGER.info("Restarting ds18b20 plugin due to change in configuration keys [{}]".format(', '.join(diff)))
    else:
        new_handle = copy.deepcopy(handle)
        new_handle['restart'] = 'no'
    return new_handle


def plugin_shutdown(handle):
    """ Shutdown the plugin and does required cleanup

    To be called prior to the South service being shut down.

    Args:
        handle: handle returned by the plugin initialisation call
    Returns:
    Raises:
    """
    # disconnect the communication with the thing
    # cleanup
    _LOGGER.info('ds18b20 poll plugin shut down.')
