#!/usr/bin/env python
# -*- coding: utf-8 -*-

import libvirt
import pyudev
from xml.etree import ElementTree
import json

libvirt_conn = libvirt.open()
hub_domains = {}


def get_usb_hostdev_xml(device):
    hostdev = ElementTree.Element('hostdev')
    hostdev.set('mode', 'subsystem')
    hostdev.set('type', 'usb')
    hostdev.set('managed', 'yes')
    source = ElementTree.SubElement(hostdev, 'source')
    vendor = ElementTree.SubElement(source, 'vendor')
    vendor.set('id', hex(int(device.attributes.get('idVendor'), 16)))
    product = ElementTree.SubElement(source, 'product')
    product.set('id', hex(int(device.attributes.get('idProduct'), 16)))
    return ElementTree.tostring(hostdev)


def vm_attach_device(domain_name, device):
    domain = libvirt_conn.lookupByName(domain_name)
    if domain.isActive():
        xml = get_usb_hostdev_xml(device)
        print('attaching {0} to {1}'.format(device.device_node, domain_name))
        domain.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_LIVE)


def usb_device_callback(device):
    if device.action == 'add':
        parent_device = device
        while True:
            parent_device = parent_device.find_parent('usb', 'usb_device')
            if parent_device is None:
                break
            elif parent_device.device_path in hub_domains:
                vm_attach_device(hub_domains[parent_device.device_path], device)
                break


def get_usb_device_paths(context, vendor_id, product_id):
    return [device.device_path for device in context.list_devices(
        subsystem='usb',
        ID_VENDOR_ID=vendor_id,
        ID_PRODUCT_ID=product_id)]


def main():
    context = pyudev.Context()
    with open('config.json', 'r') as config:
        for k, v in json.load(config).items():
            for device_path in get_usb_device_paths(context, v['idVendor'], v['idProduct']):
                hub_domains[device_path] = k
    print(hub_domains)
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by('usb', 'usb_device')
    observer = pyudev.MonitorObserver(monitor, callback=usb_device_callback)
    observer.start()
    observer.join()


if __name__ == '__main__':
    main()
