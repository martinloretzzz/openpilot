#!/usr/bin/env python

import asyncio

# pylint: disable=import-error
import websockets


async def hello():
  async with websockets.connect("ws://localhost:8765") as websocket:
    await websocket.send("Hello world!")
    while True:
      message = await websocket.recv()
      print('Rec: ', message)
      await asyncio.sleep(0.001)

asyncio.run(hello())
