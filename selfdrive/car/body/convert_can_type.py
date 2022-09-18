import struct


def long_bits_to_float(b):
  return convert_format(int(b), 'l', 'f')


def unsigned_long_bits_to_float(b):
  return convert_format(int(b), 'L', 'f')


def float_bits_to_long(b):
  return convert_format(b, 'f', 'l')


def convert_format(b, v1='l', v2='f'):
  s = struct.pack(f'>{v1}', b)
  return struct.unpack(f'>{v2}', s)[0]
