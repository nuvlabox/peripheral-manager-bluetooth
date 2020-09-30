#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""NuvlaBox Peripheral Manager Bluetooth

This service provides bluetooth device discovery.

"""

from bluepy.btle import Scanner, DefaultDelegate
# import bluetooth 
# from gattlib import DiscoveryService # Used for BLE discovery
import logging
import requests
import sys
import time
from threading import Event
import json
import converter


def init_logger():
    """ Initializes logging """

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s - %(funcName)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)


def wait_bootstrap(healthcheck_endpoint="http://agent/api/healthcheck"):
    """ Simply waits for the NuvlaBox to finish bootstrapping, by pinging the Agent API
    :returns
    """

    logging.info("Checking if NuvlaBox has been initialized...")

    r = requests.get(healthcheck_endpoint)
    
    while not r.ok:
        time.sleep(5)
        r = requests.get(healthcheck_endpoint)

    logging.info('NuvlaBox has been initialized.')
    return

def publish(url, assets):
    """
    API publishing function.
    """

    x = requests.post(url, json=assets)
    return x.json()


def send(url, assets):
    """ Sends POST request for registering new peripheral """

    logging.info("Sending Bluetooth Device information to Nuvla")
    return publish(url, assets)


def remove(url, assets):
    logging.info("Removing Bluetooth Device from Nuvla")
    x = requests.delete(url, json=assets)
    return x.json()

def bluetoothCheck(api_url, currentNetwork):
    """ Checks if peripheral already exists """

    logging.info('Checking if Bluetooth Device is already published')

    get_ethernet = requests.get(api_url + '?identifier_pattern=' + currentNetwork['identifier'])
    
    logging.info(get_ethernet.json())

    if not get_ethernet.ok or not isinstance(get_ethernet.json(), list) or len(get_ethernet.json()) == 0:
        logging.info('Bluetooth Device hasnt been published.')
        return True
    
    elif get_ethernet.json() != currentNetwork:
        logging.info('Network has changed')
        return True

    logging.info('Bluetooth device has already been published.')
    return False


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        d = {
            "available": True,
            "name": "",
            "classes": [],
            "identifier": "bluetooth-le",
            "interface": ""
        }
        if isNewDev:
            d['interface'] = dev.addr
            d['available'] = dev.connectable
            data = dev.getScanData()
            for i in data:
                if i[0] == 9:
                    d['name'] = i[-1]
                elif i[0] == 13:
                    d['classes'] = converter.convert(i[-1])
                
            send(API_URL, d)

if __name__ == "__main__":

    print('BLUETOOTH MANAGER STARTED')

    init_logger()

    API_BASE_URL = "http://agent/api"

    wait_bootstrap()

    API_URL = API_BASE_URL + "/peripheral"

    e = Event()

    scanner = Scanner().withDelegate(ScanDelegate())

    # start the scanner and keep the process running
    scanner.start()
    while True:
        scanner.process()



