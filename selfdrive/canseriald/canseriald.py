#!/usr/bin/env python3
import asyncio

# pylint ignore
import cantools
import can
import serial

import cereal.messaging as messaging
from selfdrive.canseriald.panda_emulator import emulate_panda
from util import create_periodic_task
from typing import List


dbcPath = '../../odrivebody/odrive_comma_body.dbc'
db = cantools.database.load_file(dbcPath)

odrive0_node_id = 0
odrive1_node_id = 1

imuSerialPort = "/dev/ttyACM0"
odriveSerialPort = "/dev/ttyACM1"

print_message = True

message_send_query: List[can.Message] = []

imu_serial = serial.Serial(imuSerialPort, 115200)


async def run_main():
  pm = messaging.PubMaster(["can", "pandaStates", "peripheralState"])
  sm = messaging.SubMaster(["sendcan", "can"])

  # pylint: disable=abstract-class-instantiated
  with can.interface.Bus(bustype='slcan', channel=odriveSerialPort, bitrate=250000) as bus:
    can.Notifier(bus, [handle_recieved_can_message], loop=asyncio.get_running_loop())
    # cleanup with notifier.stop()

    await asyncio.gather(
        create_periodic_task(lambda: emulate_panda(pm), 0.5),
        create_periodic_task(lambda: can_send_messages(sm, bus), frequency=500),
        create_periodic_task(lambda: publish_recieved_messages(pm), frequency=500),
        create_periodic_task(lambda: add_imu_data_to_message_querry(), frequency=100),
        create_periodic_task(lambda: request_speed(bus), frequency=90),
        create_periodic_task(lambda: request_battery(bus), frequency=2)
        # create_periodic_task(lambda: log_original_can_messages(sm), frequency=100)
    )

# Imu


def add_imu_data_to_message_querry():
  try:
    values = lineToString(imu_serial.readline()).split(" ")
    yAngle, yAngleChange = float(values[0]), float(values[1])

    message = imu_data_y_to_can_message(yAngle, yAngleChange)
    message_send_query.append(message)

    # print(message)
    # print(f"{yAngle} {yAngleChange}")
  except Exception as e:
    print(e)


def imu_data_y_to_can_message(yAngle, yAngleChange):
  y_imu_message_dbc = db.get_message_by_name('Imu_Y')
  data = y_imu_message_dbc.encode({'Angle_Y': yAngle, 'Change_Y': yAngleChange})
  return can.Message(arbitration_id=y_imu_message_dbc.frame_id, data=data, is_extended_id=False)


def lineToString(line):
  return str(line)[2:][:-5]

# Body => CAN


def can_send_messages(sm, bus):
  sm.update(0)
  if sm.updated['sendcan']:
    for capnp in sm['sendcan']:
      try:
        message = can_from_capnp(capnp)
        logMessage(message)
        bus.send(message)
      except Exception as e:
        print(e)

# CAN => Body


def publish_recieved_messages(pm):
  pm.send("can", cans_to_capnp(message_send_query))
  message_send_query.clear()

# Request Remote Message


def request_speed(bus):
  get_vel_Estimate_command = 9
  request_can_message(bus, odrive0_node_id, get_vel_Estimate_command)
  request_can_message(bus, odrive1_node_id, get_vel_Estimate_command)


def request_battery(bus):
  get_Vbus_Voltage_command = 23
  request_can_message(bus, odrive0_node_id, get_Vbus_Voltage_command)


def log_original_can_messages(sm):
  sm.update(0)
  if sm.updated['can']:
    for capnp in sm['can']:
      print(can_from_capnp(capnp))


def handle_recieved_can_message(message: can.Message) -> None:
  heartbeat_command_id = 1
  if not get_command_id(message.arbitration_id) == heartbeat_command_id:
    logMessage(message)
  message_send_query.append(message)


def request_can_message(bus: can.interface.Bus, node_id: int, command_id: int) -> None:
  message = can.Message(arbitration_id=get_arbitration_id(node_id, command_id),
                        is_remote_frame=True, is_extended_id=False)
  try:
    bus.send(message)
  except Exception as e:
    print(e)

# Util


def logMessage(message):
  if (print_message):
    # print(message)
    print(f"{message.arbitration_id}: {db.decode_message(message.arbitration_id, message.data)}")


def get_arbitration_id(node_id: int, command_id: int) -> int:
  return (node_id << 5) + command_id


def get_command_id(arbitration_id: int) -> int:
  return arbitration_id & 0b00011111


def can_from_capnp(capnp_message):
  return can.Message(arbitration_id=capnp_message.address,
                     data=bytes(capnp_message.dat), is_extended_id=False)


def cans_to_capnp(can_messages: List[can.Message]):
  msg = messaging.new_message('can', size=len(can_messages))

  for i, can_message in enumerate(can_messages):
    msg.can[i] = {"address": can_message.arbitration_id, "dat": bytes(can_message.data)}

  return msg


def main():
  asyncio.run(run_main())


if __name__ == "__main__":
  main()
