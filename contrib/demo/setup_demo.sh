#!/bin/bash

PYTHON=./bin/python
# Deactivates the password change for the demo instance
./demo/deactivate_password_change.sh

# Sets up the demo `reset` cron job (daily)
#./demo/cron_demo.sh
