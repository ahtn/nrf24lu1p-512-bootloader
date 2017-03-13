; value returned by version cmd
BOOTLOADER_VERSION_HI = 0x01
BOOTLOADER_VERSION_LO = 0x01

; usb vendor id bytes
USB_VID_HI = 0x19
USB_VID_LO = 0x15

; usb product id bytes
USB_PID_HI = 0x01
USB_PID_LO = 0x01

; CMD_NONE        = 0x00
CMD_VERSION        = 0x01
CMD_WRITE_INIT     = 0x02
CMD_READ_FLASH     = 0x03
CMD_ERASE_PAGE     = 0x04
CMD_READ_DISABLE   = 0x05
CMD_SELECT_FLASH   = 0x06
CMD_RESET          = 0x07
