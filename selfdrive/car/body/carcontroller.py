# pylint ignore
import numpy as np

from common.realtime import DT_CTRL
from opendbc.can.packer import CANPacker
from selfdrive.car.body.values import SPEED_FROM_RPM
from selfdrive.controls.lib.pid import PIDController
from selfdrive.car.body.bodycan import create_control

MAX_TORQUE = 500
MAX_TORQUE_RATE = 50
MAX_ANGLE_ERROR = np.radians(7)
MAX_POS_INTEGRATOR = 0.2   # meters
MAX_TURN_INTEGRATOR = 0.1  # meters


class CarController:
  def __init__(self, dbc_name, CP, VM):
    self.frame = 0
    self.packer = CANPacker(dbc_name)

    # Speed, balance and turn PIDs
    self.speed_pid = PIDController(0.115, k_i=0.23, rate=1/DT_CTRL)
    self.balance_pid = PIDController(1300, k_i=0, k_d=280, rate=1/DT_CTRL)
    self.turn_pid = PIDController(110, k_i=11.5, rate=1/DT_CTRL)

    self.torque_r_filtered = 0.
    self.torque_l_filtered = 0.

  @staticmethod
  def deadband_filter(torque, deadband):
    if torque > 0:
      torque += deadband
    else:
      torque -= deadband
    return torque

  def update(self, CC, CS):
    torque_l = 0
    torque_r = 0
    enabled = True  # C.enabled

    if enabled:
      angleY = CS.out.wheelSpeeds.rl  # CC.orientationNED[1]
      changeY = CS.out.wheelSpeeds.rr  # CC.angularVelocity[1]

      # Read these from the joystick
      # TODO: this isn't acceleration, okay?
      speed_desired = CC.actuators.accel / 5.
      speed_diff_desired = -CC.actuators.steer

      speed_measured = SPEED_FROM_RPM * (CS.out.wheelSpeeds.fl + CS.out.wheelSpeeds.fr) / 2.
      speed_error = speed_desired - speed_measured

      freeze_integrator = ((speed_error < 0 and self.speed_pid.error_integral <= -MAX_POS_INTEGRATOR) or
                           (speed_error > 0 and self.speed_pid.error_integral >= MAX_POS_INTEGRATOR))
      angle_setpoint = self.speed_pid.update(speed_error, freeze_integrator=freeze_integrator)

      # Clip angle error, this is enough to get up from stands
      angle_error = np.clip((-angleY) - angle_setpoint, -MAX_ANGLE_ERROR, MAX_ANGLE_ERROR)
      angle_error_rate = np.clip(-changeY, -1., 1.)
      torque = self.balance_pid.update(angle_error, error_rate=angle_error_rate)

      speed_diff_measured = SPEED_FROM_RPM * (CS.out.wheelSpeeds.fl - CS.out.wheelSpeeds.fr)
      turn_error = speed_diff_measured - speed_diff_desired
      freeze_integrator = ((turn_error < 0 and self.turn_pid.error_integral <= -MAX_TURN_INTEGRATOR) or
                           (turn_error > 0 and self.turn_pid.error_integral >= MAX_TURN_INTEGRATOR))
      torque_diff = self.turn_pid.update(turn_error, freeze_integrator=freeze_integrator)

      # Combine 2 PIDs outputs
      torque_r = torque + torque_diff
      torque_l = torque - torque_diff

      # Torque rate limits
      self.torque_r_filtered = np.clip(self.deadband_filter(torque_r, 10),
                                       self.torque_r_filtered - MAX_TORQUE_RATE,
                                       self.torque_r_filtered + MAX_TORQUE_RATE)
      self.torque_l_filtered = np.clip(self.deadband_filter(torque_l, 10),
                                       self.torque_l_filtered - MAX_TORQUE_RATE,
                                       self.torque_l_filtered + MAX_TORQUE_RATE)
      torque_r = int(np.clip(self.torque_r_filtered, -MAX_TORQUE, MAX_TORQUE))
      torque_l = int(np.clip(self.torque_l_filtered, -MAX_TORQUE, MAX_TORQUE))

    torque_r_Nm = float(torque_r) / 1000
    torque_l_Nm = float(torque_l) / 1000

    # print(f"{torque_l} {torque_l_Nm} {torque_r} {torque_r_Nm}")
    can_sends = create_control(self.packer, torque_r_Nm, torque_l_Nm)

    new_actuators = CC.actuators.copy()
    new_actuators.accel = torque_l
    new_actuators.steer = torque_r

    self.frame += 1
    return new_actuators, can_sends
