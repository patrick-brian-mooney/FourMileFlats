#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A docstring goes here, you know"""

# This series of tests is run on ping transcripts; each test looks for specific problems in the DATA passed to it and,
# if it finds problems, determines how bad the problem is and assigns a score based on the seriousness of the
# problem. Currently defined problem level scores are:
network_problem_levels = {
    0: "no impediments to normal network use",
    1: "minor problems, probably not noticeable to user",
    2: "network is usable, but is slow",
    3: "network is barely usable, and even simple tasks require a great deal of user patience",
    4: "network is essentially unusable, though it might be possible to load a web page with multiple retries",
    5: "network is completely unusable"
}

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

if __name__ == "__main__":
    pass
