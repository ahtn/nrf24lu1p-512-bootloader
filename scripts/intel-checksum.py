#!/usr/bin/env python
import sys

string = sys.argv[1]
temp = string.replace(':', '').strip()
input_bytes = [int(temp[i:i+2], base=16) for i in range(0, len(temp), 2 )]
checksum = 0x100 - (sum(input_bytes) % 256)
print(hex(checksum))
