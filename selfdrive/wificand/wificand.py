#!/usr/bin/env python3
import asyncio
import json
import typing

# pylint: disable=import-error
import websockets

import cereal.messaging as messaging

# Body DBC File:
# https://github.com/commaai/opendbc/blob/5e2a82026842a7082e5e81e5823dab6b6616dbf4/comma_body.dbc

# struct CanData {
#    address @ 0: UInt32
#    busTime @ 1: UInt16
#    dat     @ 2: Data
#    src     @ 3: UInt8
# }

CONNECTIONS: typing.Any = set()


async def main():
  async with websockets.serve(handler, "localhost", 8765):
    await can_send_main()


async def can_send_main():
  sm = messaging.SubMaster(["sendcan", "can"])

  while True:
    await asyncio.sleep(1)
    sm.update(0)

    # if sm.updated['can']:
    #     reccan = sm['can']
    #     for can in reccan:
    #       print(json_from_can_message(can))

    if sm.updated['sendcan']:
      sendcan = sm['sendcan']
      for can in sendcan:
        print(json_from_can_message(can))
        send_can_message(can)


def send_can_message(can):
  message = json_from_can_message(can)
  websockets.broadcast(CONNECTIONS, message)


def json_from_can_message(can):
  message = {
      "address": can.address,
      "busTime": can.busTime,
      "dat": bytes(can.dat).hex(),
      "src": can.src
  }
  return json.dumps(message)


async def handler(websocket):
  register(websocket)


async def register(websocket):
  CONNECTIONS.add(websocket)
  try:
    await websocket.wait_closed()
  finally:
    CONNECTIONS.remove(websocket)

if __name__ == "__main__":
  asyncio.run(main())
