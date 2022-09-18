from cereal import car
from opendbc.can.parser import CANParser
from selfdrive.car.interfaces import CarStateBase
from selfdrive.car import dbc_dict
from selfdrive.car.body.convert_can_type import long_bits_to_float, unsigned_long_bits_to_float

STARTUP_TICKS = 100


class CarState(CarStateBase):

  def update(self, cp):
    ret = car.CarState.new_message()

    ret.wheelSpeeds.fl = long_bits_to_float(cp.vl['Get_Encoder_Estimates_L']['Vel_Estimate'])
    ret.wheelSpeeds.fr = long_bits_to_float(cp.vl['Get_Encoder_Estimates_R']['Vel_Estimate'])
    # use back wheels to save the angle and angle_change
    ret.wheelSpeeds.rl = unsigned_long_bits_to_float(cp.vl['Imu_Y']['Angle_Y'])
    ret.wheelSpeeds.rr = unsigned_long_bits_to_float(cp.vl['Imu_Y']['Change_Y'])

    ret.vEgoRaw = ((ret.wheelSpeeds.fl + ret.wheelSpeeds.fr) / 2.) * self.CP.wheelSpeedFactor

    ret.vEgo, ret.aEgo = self.update_speed_kf(ret.vEgoRaw)
    ret.standstill = False

    ret.steerFaultPermanent = any([cp.vl['Heartbeat_L']['Axis_Error'], cp.vl['Heartbeat_R']['Axis_Error']])

    voltage = long_bits_to_float(cp.vl['Get_Vbus_Voltage_L']['Vbus_Voltage'])
    ret.charging = voltage > 14
    ret.fuelGauge = self.get_battery_percent(voltage, serial_battery_count=4)

    # print(str(voltage) + " " + str(ret.fuelGauge))

    # irrelevant for non-car
    ret.gearShifter = car.CarState.GearShifter.drive
    ret.cruiseState.enabled = True
    ret.cruiseState.available = True

    return ret

  def get_battery_percent(self, voltage, serial_battery_count=12):
    battery_full = 4.2 * serial_battery_count
    battery_empty = 3.5 * serial_battery_count

    battery_percent = (voltage - battery_empty) / (battery_full - battery_empty)
    battery_percent_claped = max(min(battery_percent, 1.0), 0.0)

    return battery_percent_claped

  @staticmethod
  def get_can_parser(CP):
    dbc = dbc_dict('../odrivebody/odrive_comma_body', None)["pt"]

    signals = [
        # sig_name, sig_address
        ("Vel_Estimate", "Get_Encoder_Estimates_L"),
        ("Vel_Estimate", "Get_Encoder_Estimates_R"),
        ("Axis_Error", "Heartbeat_L"),
        ("Axis_Error", "Heartbeat_R"),
        ("Vbus_Voltage", "Get_Vbus_Voltage_L"),
        ("Angle_Y", "Imu_Y"),
        ("Change_Y", "Imu_Y"),
    ]

    checks = [
        ("Get_Encoder_Estimates_L", 25),
        ("Get_Encoder_Estimates_R", 25),
        ("Heartbeat_L", 5),
        ("Heartbeat_R", 5),
        ("Get_Vbus_Voltage_L", 1),
        ("Imu_Y", 100),
    ]

    return CANParser(dbc, signals, checks, 0)
