#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This module handles report creation for Patrick Mooney's program
network-reporter. Like the rest of network-reporter, this module is copyright
2017 by Patrick Mooney. It is licensed under the GNU GPL, either version 3 or,
at your option, any later version. See the file LICENSE for details.
"""


import pickle

from config import *


# Once all of the usability tests have been run, the overall network problem score is the largest problem score
# assigned by any test that the ping transcript has failed. (The operating theory here is we should be recording the
# level of the problem that has the biggest impact on usability.

usability_tests = [
    {'test_name': 'Packet loss above 1%',
     'test': lambda data: int(data['packet loss'].strip().strip('%').strip()) > 1,
     'problem_level': 1,
     'data_keys_to_report': ['packet loss']},
    {'test_name': 'Packet loss above 3%',
     'test': lambda data: int(data['packet loss'].strip().strip('%').strip()) > 3,
     'problem_level': 2,
     'data_keys_to_report': ['packet loss']},
    {'test_name': 'Packet loss above 6%',
     'test': lambda data: int(data['packet loss'].strip().strip('%').strip()) > 6,
     'problem_level': 3,
     'data_keys_to_report': ['packet loss']},
    {'test_name': 'Packet loss above 13%',
     'test': lambda data: int(data['packet loss'].strip().strip('%').strip()) > 13,
     'problem_level': 4,
     'data_keys_to_report': ['packet loss']},
    {'test_name': 'Packet loss above 25%',
     'test': lambda data: int(data['packet loss'].strip().strip('%').strip()) > 25,
     'problem_level': 5,
     'data_keys_to_report': ['packet loss']},

    {'test_name': 'Average packet RTT above 200 ms',
     'test': lambda data: float(data['avg']) > 200,
     'problem_level': 1,
     'data_keys_to_report': ['avg']},
    {'test_name': 'Average packet RTT above 500 ms',
     'test': lambda data: float(data['avg']) > 500,
     'problem_level': 2,
     'data_keys_to_report': ['avg']},
    {'test_name': 'Average packet RTT above 1000 ms',
     'test': lambda data: float(data['avg']) > 1000,
     'problem_level': 3,
     'data_keys_to_report': ['avg']},
    {'test_name': 'Average packet RTT above 2000 ms',
     'test': lambda data: float(data['avg']) > 2000,
     'problem_level': 4,
     'data_keys_to_report': ['avg']},
    {'test_name': 'Average packet RTT above 5000 ms',
     'test': lambda data: float(data['avg']) > 5000,
     'problem_level': 5,
     'data_keys_to_report': ['avg']},

    {'test_name': 'Jitter above 100%',
     'test': lambda data: (float(data['mdev'].strip().strip('ms').strip()) / float(data['avg']) ) > 1,
     'problem_level': 1,
     'data_keys_to_report': ['mdev', 'avg']},
    {'test_name': 'Jitter above 150%',
     'test': lambda data: (float(data['mdev'].strip().strip('ms').strip()) / float(data['avg']) ) > 1.5,
     'problem_level': 2,
     'data_keys_to_report': ['mdev', 'avg']},
    {'test_name': 'Jitter above 200%',
     'test': lambda data: (float(data['mdev'].strip().strip('ms').strip()) / float(data['avg']) ) > 2,
     'problem_level': 3,
     'data_keys_to_report': ['mdev', 'avg']},
    {'test_name': 'Jitter above 250%',
     'test': lambda data: (float(data['mdev'].strip().strip('ms').strip()) / float(data['avg']) ) > 2.5,
     'problem_level': 4,
     'data_keys_to_report': ['mdev', 'avg']},
    {'test_name': 'Jitter above 300%',
     'test': lambda data: (float(data['mdev'].strip().strip('ms').strip()) / float(data['avg']) ) > 3,
     'problem_level': 5,
     'data_keys_to_report': ['mdev', 'avg']},
]

def daily_report_template():
    """Returns an HTML template for the daily reports. This template will include
    percent-codes for information to be filled in by the calling function.
    """
    ret = """<!doctype html>
<head>
<meta charset="utf-8" />
<link rel="profile" href="http://microformats.org/profile/hcalendar" />

"""
    ret += ""
    ret += """
<title>Network report for %s</title>    <!-- current date -->
</head>
<body>
</body>
</html>
"""
    return ret

def produce_daily_report(datafile):
    """Produces an HTML report summarizing the day's activity. Stores it in the
    appropriate part of the local filesystem.
    """
    with open(datafile, mode="rb") as data_store:
        daily_data = pickle.load(data_store.read())


if __name__ == "__main__":
    pass
