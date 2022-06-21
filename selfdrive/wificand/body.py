#!/usr/bin/env python
import asyncio
import json

# pylint: disable=import-error
import websockets

# Example can data:
# 0201( 513)(   548)(100Hz) 000000082c68091c
# 0202(514)(55)(10Hz) 030000
# 0203(515)(6)(1Hz) 010af698
# 0204(516)(548)(100Hz) 0000000afff60017


WEBSOCKETURL = "ws://localhost:8765"


async def main():
  async with websockets.connect(WEBSOCKETURL) as websocket:
    await asyncio.gather(
        asyncio.create_task(recieve_task(websocket)),
        asyncio.create_task(send_task(websocket))
    )


async def recieve_task(websocket):
  while True:
    message = await websocket.recv()
    print('> ', message)
    await asyncio.sleep(0.001)


async def send_task(websocket):
  while True:
    print("> send state")
    await send_can_messages(websocket, [
        {"address": 513, "dat": "000000082c68091c"},
        {"address": 514, "dat": "030000"},
        {"address": 515, "dat": "010af698"},
        {"address": 516, "dat": "0000000afff60017"}
    ])
    await asyncio.sleep(0.1)


async def send_can_messages(websocket, messages):
  await websocket.send(json.dumps(messages))


asyncio.run(main())
