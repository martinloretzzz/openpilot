from selfdrive.car.body.convert_can_type import float_bits_to_long


def create_control(packer, torque_l, torque_r):
  left_package = packer.make_can_msg("Set_Input_Torque_L", 0, {"Input_Torque": float_bits_to_long(torque_l)})
  right_package = packer.make_can_msg("Set_Input_Torque_R", 0, {"Input_Torque": float_bits_to_long(torque_r)})

  return left_package, right_package
