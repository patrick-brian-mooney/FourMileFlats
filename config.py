#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This module contains configuration constants for Patrick Mooney's
network-reporter program. Like the rest of network-reporter, this module is
copyright 2017 by Patrick Mooney. It is licensed under the GNU GPL, either
version 3 or, at your option, any later version. See the file LICENSE for
details.
"""

# PING configuration parameters
ping_exec = "/bin/ping"     # Put the full path to your PING executable here.
ping_count_flag = "-c %d"   # The flag to supply to tell the PING executable how many times to ping the remote host. Add a %d
                            # after it so the number of attempts can be substituted in.

# Who, how often, and how long to ping
ping_target = "google.com"  # Which host to ping?
interval_between_pings = 5  # Number of minutes between the beginning of one check and the beginning of the next
number_of_packets = 100     # How many ping packets to send during each check

# Locations in the local filesystem.
data_location = "data/"                                             # Where are we storing raw data?
reports_location = "reports/"                                       # Reports are kept here, in subfolders organized year/month/


# When the  series of tests is run on ping transcripts; each test looks for specific problems in the DATA passed to it
# and, if it finds problems, determines how bad the problem is and assigns a score based on the seriousness of the
# problem. Currently defined problem level scores are:
network_problem_levels = {
    0: "no impediments to normal network use",
    1: "minor problems, probably only noticeable to gamers",
    2: "network is usable, but is slow",
    3: "network is barely usable, and even simple tasks require a great deal of user patience",
    4: "network is essentially unusable, though it might be possible to load a web page with multiple retries",
    5: "network is completely unusable"
}
