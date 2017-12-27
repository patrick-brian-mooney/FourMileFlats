#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A utility script to convert the data collected by Patrick Mooney's
network_monitor scripts into a human-readable form. This output is similar to,
but is not actually, the JSON format.

Usage:
    ./dump_data.py FILENAME

where FILENAME is the name of a data file produced by the monitor.py script.
Note that dump_data.py just decodes the data to your terminal; use shell
redirection if you need to dump to a file.

This utility script is copyright 2017 by Patrick Mooney. It is part of Patrick
Mooney's network_monitor utility, and like the project of which it is a part)
is released under the GNU GPL, either version 3 or (at your option) any later
version.

See https://github.com/patrick-brian-mooney/network-reporter for more
information or to file a bug report.
"""

import pickle, pprint, sys

import monitor


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ERROR: You must specify an input file")
        sys.exit(1)
    if sys.argv[1] in ['-h', '--help']:
        print(__doc__)
        sys.exit()
    pprint.pprint(monitor.get_data_store(which_store=sys.argv[1]))

