#!/bin/env python
import usb.core
import usb.util
import time
import bootloader
import sys

ID_VENDOR = 0x1915
ID_PRODUCT = 0x0101

debug = True

# def usb_setup():
# dev = usb.core.find()
dev = usb.core.find(idVendor=ID_VENDOR, idProduct=ID_PRODUCT)

reattach = False
if dev.is_kernel_driver_active(1):
    reattach = True
    dev.detach_kernel_driver(1)

cfg = dev.get_active_configuration()
intf = cfg[(0,0)]

ep1in = usb.util.find_descriptor(
    intf,
    # match the first OUT endpoint
    custom_match = \
    lambda e: \
        e.bEndpointAddress == 0x81)
ep1out = usb.util.find_descriptor(
    intf,
    # match the first OUT endpoint
    custom_match = \
    lambda e: \
        e.bEndpointAddress == 0x01)

if False:
    print("cfg: ")
    print(cfg)
    print("\n intf:")
    print(intf)
    print("\n ep1out:")
    print(ep1out)
    print("\n ep1in:")
    print(ep1in)
    print("0x{:x} 0x{:x}".format(ep1in.bEndpointAddress, ep1in.wMaxPacketSize))

# def usb_cleanup():
#     # It may raise USBError if there's e.g. no kernel driver loaded at all
#     if reattach:
#         dev.attach_kernel_driver(1)

# It may raise USBError if there's e.g. no kernel driver loaded at all
if reattach:
    dev.attach_kernel_driver(1)


def print_cmd_sent(name, cmd):
    print("cmd: {} \t raw_cmd: {}".format(name, cmd) )

def flash_erase_all():
    for i in range(32):
        flash_erase(i)

def bytes_to_str(byte_array):
    return ''.join(["{:02x}".format(byte) for byte in byte_array])

def usb_cmd(cmd, arg=None):
    raw_cmd = bytes([cmd])
    if arg != None:
        raw_cmd = bytes([cmd, arg])
    print_cmd_sent("", raw_cmd)
    ep1out.write(raw_cmd)

def usb_cmd_recv_zero(cmd):
    return read_usb_in() != 0x00

def read_usb_in():
    data = ep1in.read(64, 1000)
    return data

def print_usb_response():
    data = ep1in.read(64, 1000)
    print(bytes_to_str(data))
    return data

def bootloader_version():
    usb_cmd(bootloader.CMD_VERSION)
    return print_usb_response()

def flash_read_disable():
    usb_cmd(bootloader.CMD_READ_DISABLE)
    return print_usb_response()

def flash_read_block(block):
    usb_cmd(bootloader.CMD_READ_FLASH, block)
    return print_usb_response()

def flash_erase_page(page_num):
    usb_cmd(bootloader.CMD_ERASE_PAGE, page_num)
    return print_usb_response()

def flash_select_half(half):
    usb_cmd(bootloader.CMD_SELECT_FLASH, half)
    return print_usb_response()

def flash_write_page(page_num, page):
    usb_cmd(bootloader.CMD_WRITE_INIT, page_num)

    for block in [page[i:i+64] for i in range(0, 512, 64)]:
        ep1out.write(block)
        ep1in.read(64, 10000)

def flash_print_all(size=16):
    flash_select_half(0)
    for i in range(256):
        flash_read_block(i)
    if size == 32:
        flash_select_half(1)
        for i in range(256):
            flash_read_block(i)

import sys
test = int(sys.argv[1])

if test == 0:
    flash_print_all()
if test == 1:
    flash_select_half(0)
    flash_write_page(1, bytes([i%256 for i in range(512)]))

    flash_read_block(0)
    flash_read_block(8)
    flash_read_block(9)
elif test == 2:
    flash_select_half(0)

    flash_read_block(0)
    flash_read_block(8)
    flash_read_block(9)

    flash_write_page(1, bytes([0]+[0xff for i in range(511)]))

    flash_read_block(0)
    flash_read_block(8)
    flash_read_block(9)

elif test == 3:
    flash_read_block(0x00)
    flash_read_block(0x08)
    flash_read_block(0x10)
    flash_read_disable()
    flash_write_page(1, bytes([0]+[0xff for i in range(511)]))
    flash_read_block(0x00)
    flash_read_block(0x08)
    flash_read_block(0x10)
    flash_write_page(2, bytes([0]+[0xff for i in range(511)]))
    flash_read_block(0x00)
    flash_read_block(0x08)
    flash_read_block(0x10)

elif test == 4:
    pass

# It may raise USBError if there's e.g. no kernel driver loaded at all
if reattach:
    dev.attach_kernel_driver(1)
