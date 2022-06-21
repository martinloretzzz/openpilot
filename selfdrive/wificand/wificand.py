#!/usr/bin/env python3
# pylint: disable=import-error
import asyncio
import json
from typing import Any

import websockets

import cereal.messaging as messaging
from selfdrive.wificand.panda_emulator import emulate_panda_task

# Body DBC File:
# https://github.com/commaai/opendbc/blob/5e2a82026842a7082e5e81e5823dab6b6616dbf4/comma_body.dbc

# Start body without fingerprinting:
# export SKIP_FW_QUERY=1 && export FINGERPRINT="COMMA BODY" && python manager.py

CONNECTIONS: Any = set()


async def run_main():
  pm = messaging.PubMaster(["can", "pandaStates", "peripheralState"])
  sm = messaging.SubMaster(["sendcan", "can"])
  async with websockets.serve(lambda ws: handler(ws, pm), "localhost", 8765):
    await asyncio.gather(
        asyncio.create_task(emulate_panda_task(pm)),
        asyncio.create_task(can_send_task(sm))
        # asyncio.create_task(log_original_can_messages_task(sm))
    )


async def can_send_task(sm):
  while True:
    sm.update(0)

    if sm.updated['sendcan']:
      for can in sm['sendcan']:
        # print("Send:", can_to_json(can))
        send_can_message(can)
    await asyncio.sleep(0.01)


async def log_original_can_messages_task(sm):
  while True:
    sm.update(0)
    if sm.updated['can']:
      for can in sm['can']:
        print(can_to_json(can))
    await asyncio.sleep(0.01)


def send_can_message(can):
  message = can_to_json(can)
  websockets.broadcast(CONNECTIONS, message)


async def handler(websocket, pm):
  CONNECTIONS.add(websocket)
  while True:
    try:
      message = await websocket.recv()
    except websockets.ConnectionClosedOK:
      CONNECTIONS.remove(websocket)
      break
    handle_recieved_message(pm, message)


def handle_recieved_message(pm, websocket):
  # print("Rec :", websocket)
  messages = json_to_can(websocket)
  pm.send("can", messages)


def json_to_can(cans_str):
  can_messages = json.loads(cans_str)
  msg = messaging.new_message('can', size=len(can_messages))
  for i, can in enumerate(can_messages):
    can["dat"] = bytes(bytearray.fromhex(can["dat"]))
    msg.can[i] = can
  return msg


def can_to_json(can):
  return json.dumps({
      "address": can.address,
      "busTime": can.busTime,
      "dat": bytes(can.dat).hex(),
      "src": can.src
  })


def main():
  asyncio.run(run_main())


if __name__ == "__main__":
  main()
