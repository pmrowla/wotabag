#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
import functools
import logging

from . import exceptions
from . import adapters
from .gatt_server import WotabagService


logger = logging.getLogger('wotabag')


BLUEZ_SERVICE_NAME = 'org.bluez'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'

LE_ADVERTISEMENT_IFACE = 'org.bluez.LEAdvertisement1'


class Advertisement(dbus.service.Object):
    PATH_BASE = '/org/bluez/example/advertisement'

    def __init__(self, bus, index, advertising_type):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.ad_type = advertising_type
        self.service_uuids = None
        self.manufacturer_data = None
        self.solicit_uuids = None
        self.service_data = None
        self.include_tx_power = None
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        properties = dict()
        properties['Type'] = self.ad_type
        if self.service_uuids is not None:
            properties['ServiceUUIDs'] = dbus.Array(self.service_uuids,
                                                    signature='s')
        if self.solicit_uuids is not None:
            properties['SolicitUUIDs'] = dbus.Array(self.solicit_uuids,
                                                    signature='s')
        if self.manufacturer_data is not None:
            properties['ManufacturerData'] = dbus.Dictionary(
                self.manufacturer_data, signature='qv')
        if self.service_data is not None:
            properties['ServiceData'] = dbus.Dictionary(self.service_data,
                                                        signature='sv')
        if self.include_tx_power is not None:
            properties['IncludeTxPower'] = dbus.Boolean(self.include_tx_power)
        return {LE_ADVERTISEMENT_IFACE: properties}

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service_uuid(self, uuid):
        if not self.service_uuids:
            self.service_uuids = []
        self.service_uuids.append(uuid)

    def add_solicit_uuid(self, uuid):
        if not self.solicit_uuids:
            self.solicit_uuids = []
        self.solicit_uuids.append(uuid)

    def add_manufacturer_data(self, manuf_code, data):
        if not self.manufacturer_data:
            self.manufacturer_data = dbus.Dictionary({}, signature='qv')
        self.manufacturer_data[manuf_code] = dbus.Array(data, signature='y')

    def add_service_data(self, uuid, data):
        if not self.service_data:
            self.service_data = dbus.Dictionary({}, signature='sv')
        self.service_data[uuid] = dbus.Array(data, signature='y')

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        logger.debug('GetAll')
        if interface != LE_ADVERTISEMENT_IFACE:
            raise exceptions.InvalidArgsException()
        logger.debug('returning props')
        return self.get_properties()[LE_ADVERTISEMENT_IFACE]

    @dbus.service.method(LE_ADVERTISEMENT_IFACE,
                         in_signature='',
                         out_signature='')
    def Release(self):
        logger.debug('{}: Released!'.format(self.path))


class WotabagAdvertisement(Advertisement):

    def __init__(self, bus, index):
        """Initialize BLE GATT advertisement for a Wotabag.

        GATT service will identify itself with the following parameters:

            Vendor/Manufacturer:
                ID: 0xffff (reserved value for default vendor ID)
                Data: ['W', 'O', 'T', 'A', 'B', 'A', 'G']

            Available service UUID's:
                0x1804: reserved Tx Power service
                0x0715: Wotabag RPC

        """
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid(WotabagService.WOTABAG_SVC_UUID)

        # (0xffff, ['W', 'O', 'T', 'A', 'B', 'A', 'G'])
        self.add_manufacturer_data(0xffff, [0x57, 0x4f, 0x74, 0x41, 0x42, 0x41, 0x47])
        self.include_tx_power = True


def register_ad_cb():
    logger.info('Advertisement registered')


def register_ad_error_cb(mainloop, error):
    logger.error('Failed to register advertisement: ' + str(error))
    mainloop.quit()


def advertising_main(mainloop, bus, adapter_name):
    adapter = adapters.find_adapter(bus, LE_ADVERTISING_MANAGER_IFACE, adapter_name)
    logger.info('adapter: %s' % (adapter,))
    if not adapter:
        raise Exception('LEAdvertisingManager1 interface not found')

    adapter_props = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                   "org.freedesktop.DBus.Properties")

    adapter_props.Set("org.bluez.Adapter1", "Powered", dbus.Boolean(1))

    ad_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                LE_ADVERTISING_MANAGER_IFACE)

    test_advertisement = WotabagAdvertisement(bus, 0)

    ad_manager.RegisterAdvertisement(test_advertisement.get_path(), {},
                                     reply_handler=register_ad_cb,
                                     error_handler=functools.partial(register_ad_error_cb, mainloop))
