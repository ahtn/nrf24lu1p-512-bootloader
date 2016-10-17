#!/bin/env python
import usb.core
import usb.util
import time
import bootloader
import sys
import intelhex

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
    # print("cmd: {} \t raw_cmd: {}".format(name, cmd) )
    # print("cmd: {} \t raw_cmd: {}".format(name, cmd) )
    pass

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

def usb_get_response():
    # todo error handling
    return ep1in.read(64, 1000)

def bootloader_version():
    usb_cmd(bootloader.CMD_VERSION)
    return print_usb_response()

def flash_read_disable():
    usb_cmd(bootloader.CMD_READ_DISABLE)
    return print_usb_response()

def flash_read_block(block):
    usb_cmd(bootloader.CMD_READ_FLASH, block)
    return usb_get_response()

def flash_erase_page(page_num):
    usb_cmd(bootloader.CMD_ERASE_PAGE, page_num)
    return print_usb_response()

def flash_select_half(half):
    usb_cmd(bootloader.CMD_SELECT_FLASH, half)
    return usb_get_response()

def flash_write_page(page_num, page):
    usb_cmd(bootloader.CMD_WRITE_INIT, page_num)

    for a,b in [(i,i+64) for i in range(0, 512, 64)]:
        block = page[a:b]
        if len(block) < 64:
            block += bytes([0xff] * (64 - len(block)))
        ep1out.write(block)
        ep1in.read(64, 10000)

def is_empty_flash_data(data):
    for b in data:
        if b != 0xff:
            return False
    return True

def chunk_iterator(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

def flash_read_to_hex(size=16):
    # result = []
    if size not in [16, 32]:
        raise Exception("Cannot read flash size {} only 16 or 32".format(size))

    page_size = 0x200
    block_size = 0x40
    blocks_per_16kb = 0x100
    hexfile = intelhex.IntelHex()
    cur_addr = 0x0000

    def read_16kb_region():
        chunks_per_block = 4
        chunk_size = block_size // chunks_per_block
        nonlocal cur_addr
        for i in range(blocks_per_16kb):
            block = flash_read_block(i)
            # break the block into chunks to we can check which regions
            # actuall have flash data
            for chunk in chunk_iterator(block, chunk_size):
                if not is_empty_flash_data(chunk):
                    hexfile.puts(cur_addr, bytes(chunk))
                cur_addr += chunk_size

    flash_select_half(0)
    read_16kb_region()
    if size == 32:
        flash_select_half(1)
        read_16kb_region()
    return hexfile

def hex_dump(data):
    addr = 0
    for block in [data[i:i+64] for i in range(0, len(data), 64)]:
        print("{:04x}".format(addr), bytes_to_str(block))
        addr += 64

import sys
arg = sys.argv[1]

# TODO: cleanup cmd line handling
outfile = "readback.hex"

if arg == "read_16":
    ihex = flash_read_to_hex(size=16)
    ihex.dump()
    ihex.tofile(outfile, "hex")

elif arg == "read_32":
    ihex = flash_read_to_hex(size=32)
    ihex.dump()
    ihex.tofile(outfile, "hex")

elif arg == "write_hex":
    flash_size = 0x8000
    page_size = 0x0200
    num_pages = flash_size // page_size

    hexfile = intelhex.IntelHex()
    hexfile.loadhex(sys.argv[2])
    if hexfile.maxaddr() > flash_size:
        raise "hexfile too large"

    hexfile.padding = 0xff
    data = hexfile.tobinarray(start=0x0000, end=flash_size)

    for page_num in range(0, num_pages):
        page_start = page_num * page_size
        page_end = (page_num+1) * page_size
        page_data = data[page_start:page_end]

        is_empty_page = True
        for b in page_data:
            if b != 0xff:
                is_empty_page = False
                break
        if is_empty_page:
            continue

        # print("{:x} {:x} {:x} {}".format(page_start, page_end, len(page_data), page_data))

        flash_write_page(page_num, page_data)

elif arg == "zero_all":
    for i in range(64):
        flash_write_page(i, bytes([0]*512))

elif arg == "read_disable":
    flash_read_disable()

elif arg == "new_cmd":
    pass

# It may raise USBError if there's e.g. no kernel driver loaded at all
if reattach:
    print("reattach")
    dev.attach_kernel_driver(1)
