#!/usr/bin/bash

export SKIP_FW_QUERY=1
export FINGERPRINT="COMMA BODY"
export PASSIVE="0"

chmod 666 /dev/ttyACM0

exec ./launch_chffrplus.sh

