#!/usr/bin/env python
# -*- coding: utf-8 -*-

import libvirt
import pyudev
from xml.etree import ElementTree

libvirt_conn = libvirt.open()
hub_domains = {}


def get_usb_hostdev_xml(dev_node):
    hostdev = ElementTree.Element('hostdev')
    hostdev.set('mode', 'subsystem')
    hostdev.set('type', 'usb')
    source = ElementTree.SubElement(hostdev, 'source')
    source.set('dev', dev_node)
    return ElementTree.tostring(hostdev)


def vm_attach_device(domain_name, device):
    domain = libvirt_conn.lookupByName(domain_name)
    if domain.isActive():
        print('attaching {0} to {1}'.format(device.device_node, domain_name))
        xml = get_usb_hostdev_xml(device.device_node)
        domain.attachDeviceFlags(xml, libvirt.VIR_DOMAIN_AFFECT_LIVE)
        print(xml)


def usb_device_callback(device):
    if device.action == 'add':
        parent_device = device
        while True:
            parent_device = parent_device.find_parent('usb', 'usb_device')
            if parent_device == None:
                break
            elif parent_device.device_path in hub_domains:
                vm_attach_device(hub_domains[parent_device.device_path], device)
                break


def get_usb_device_paths(context, vendor_id, product_id):
    device_paths = []
    for device in context.list_devices(
            subsystem='usb',
            ID_VENDOR_ID=vendor_id,
            ID_PRODUCT_ID=product_id
    ):
        device_paths.append(device.device_path)
    return device_paths


def main():
    context = pyudev.Context()
    for device_path in get_usb_device_paths(context, '05e3', '0608'):
        hub_domains[device_path] = 'singapore'
    print(hub_domains)
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by('usb', 'usb_device')
    observer = pyudev.MonitorObserver(monitor, callback=usb_device_callback)
    observer.start()
    observer.join()


if __name__ == '__main__':
    main()
