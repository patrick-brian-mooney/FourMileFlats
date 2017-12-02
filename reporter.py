#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""network_reporter.py is a script that produces reports on the health of my
Internet connection at home.

This program comes with no warranty at all, and the author discliams any
responsibility for what it may do on your computer. This is ALPHA SOFTWARE.
Use at your own risk.

This program is copyright 2017 by Patrick Mooney. It is licensed under the GNU
general public license, either version 3 or (at your option) any later version.
See the file LICENSE for more details.
"""

import subprocess

import patrick_logger       # https://github.com/patrick-brian-mooney/python-personal-library
from patrick_logger import log_it

patrick_logger.verbosity_level = 2


ping_exec = "/bin/ping"     # Put the full path to your PING executable here.
ping_count_flag = "-c %d"   # The flag to supply to tell the PING executable how many times to ping the remote host. Add a %d
                            # after it so the number of attempts can be substituted in.
number_of_packets = 60      # How many ping packets to send during each check
ping_target = "google.com"  # Which host to ping?
interval_between_pings = 5  # Number of minutes between the beginning of one check and the beginning of the next


def check_ping_config():
    try:
        ping_command = "%s %s %s" % (ping_exec, ping_count_flag % 1, ping_target)
        _ = subprocess.check_output(ping_command, shell=True)
        log_it("INFO: successfully ran the test ping command `%s`" % ping_command, 2)
    except BaseException:
        log_it("ERROR: unable to check ping configuration.")
        log_it("       Please check the ping configuration at the top of reporter.py")    

def startup():
    check_ping_config()

if __name__ == "__main__":
    startup()
