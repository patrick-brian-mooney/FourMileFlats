#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This module handles report creation for Patrick Mooney's program
network-reporter. Like the rest of network-reporter, this module is copyright
2017 by Patrick Mooney. It is licensed under the GNU GPL, either version 3 or,
at your option, any later version. See the file LICENSE for details.
"""


import datetime, glob, inspect, os, pickle, statistics

from config import *

import patrick_logger       # https://github.com/patrick-brian-mooney/python-personal-library
from patrick_logger import log_it


# Once all of the usability tests have been run, the overall network problem score is the largest problem score
# assigned by any test that the ping transcript has failed. (The operating theory here is we should be recording the
# level of the problem that has the biggest impact on usability.)

usability_tests = [
    {'test_name': 'Packet loss at least 1%',
     'test': lambda data: int(data['packet_loss'].strip().strip('%').strip()) >= 1,
     'problem_level': 1,
     'data_keys_to_report': ['packet_loss'],
     'test_group': 'packet_loss'},
    {'test_name': 'Packet loss at least 3%',
     'test': lambda data: int(data['packet_loss'].strip().strip('%').strip()) >= 3,
     'problem_level': 2,
     'data_keys_to_report': ['packet_loss'],
     'test_group': 'packet_loss'},
    {'test_name': 'Packet loss at least 6%',
     'test': lambda data: int(data['packet_loss'].strip().strip('%').strip()) >= 6,
     'problem_level': 3,
     'data_keys_to_report': ['packet_loss'],
     'test_group': 'packet_loss'},
    {'test_name': 'Packet loss at least 13%',
     'test': lambda data: int(data['packet_loss'].strip().strip('%').strip()) >= 13,
     'problem_level': 4,
     'data_keys_to_report': ['packet_loss'],
     'test_group': 'packet_loss'},
    {'test_name': 'Packet loss at least 25%',
     'test': lambda data: int(data['packet_loss'].strip().strip('%').strip()) >= 25,
     'problem_level': 5,
     'data_keys_to_report': ['packet_loss'],
     'test_group': 'packet_loss'},

    {'test_name': 'Average packet RTT above 200 ms',
     'test': lambda data: float(data['avg']) > 200,
     'problem_level': 1,
     'data_keys_to_report': ['avg'],
     'test_group': 'high RTT'},
    {'test_name': 'Average packet RTT above 500 ms',
     'test': lambda data: float(data['avg']) > 500,
     'problem_level': 2,
     'data_keys_to_report': ['avg'],
     'test_group': 'high RTT'},
    {'test_name': 'Average packet RTT above 1000 ms',
     'test': lambda data: float(data['avg']) > 1000,
     'problem_level': 3,
     'data_keys_to_report': ['avg'],
     'test_group': 'high RTT'},
    {'test_name': 'Average packet RTT above 2000 ms',
     'test': lambda data: float(data['avg']) > 2000,
     'problem_level': 4,
     'data_keys_to_report': ['avg'],
     'test_group': 'high RTT'},
    {'test_name': 'Average packet RTT above 5000 ms',
     'test': lambda data: float(data['avg']) > 5000,
     'problem_level': 5,
     'data_keys_to_report': ['avg'],
     'test_group': 'high RTT'},

    {'test_name': 'Jitter above 200%',
     'test': lambda data: (float(data['mdev'].strip().strip('ms').strip()) / float(data['avg']) ) > 2,
     'problem_level': 1,
     'data_keys_to_report': ['mdev', 'avg'],
     'test_group': 'high jitter'},
    {'test_name': 'Jitter above 300%',
     'test': lambda data: (float(data['mdev'].strip().strip('ms').strip()) / float(data['avg']) ) > 3,
     'problem_level': 2,
     'data_keys_to_report': ['mdev', 'avg'],
     'test_group': 'high jitter'},
    {'test_name': 'Jitter above 400%',
     'test': lambda data: (float(data['mdev'].strip().strip('ms').strip()) / float(data['avg']) ) > 4,
     'problem_level': 3,
     'data_keys_to_report': ['mdev', 'avg'],
     'test_group': 'high jitter'},
    {'test_name': 'Jitter above 500%',
     'test': lambda data: (float(data['mdev'].strip().strip('ms').strip()) / float(data['avg']) ) > 5,
     'problem_level': 4,
     'data_keys_to_report': ['mdev', 'avg'],
     'test_group': 'high jitter'},
    {'test_name': 'Jitter above 600%',
     'test': lambda data: (float(data['mdev'].strip().strip('ms').strip()) / float(data['avg']) ) > 6,
     'problem_level': 5,
     'data_keys_to_report': ['mdev', 'avg'],
     'test_group': 'high jitter'},

    {'test_name': 'Fundamental networking errors',
     'test': lambda data: 'errors' in data,
     'problem_level': 4,
     'data_keys_to_report': ['errors'],
     'test_group': 'unreachable'},
]


def monthly_report_template():
    """Returns a markdown template for monthly reports. The template includes %-codes
    to be filled in by the calling function.
    """
    ret = """# Monthly Network Quality Summary for %s during %s

## Summary 

%s

## Daily logs

%s
""" # Substitute in: Situation; Month-Year; monthly summary data; links to daily ping and traceroute logs.
    return ret


def tests_failed_list(daily_data_dict):
    """Returns a summary list of all tests failed during the month, organized by
    category.
    """
    ret = ""
    event_counts = dict()
    for day in daily_data_dict:
        for event in daily_data_dict[day]['usability_events']:
            for test in daily_data_dict[day]['usability_events'][event]['tests_failed']:
                if test['test_failed'] in event_counts:
                    event_counts[test['test_failed']] += 1
                else:
                    event_counts[test['test_failed']] = 1
    for event_type in sorted(event_counts.keys()):
        ret += "%s: %d occurrences\n" % (event_type, event_counts[event_type])
    ret += "\nTotal tests failed: %d\n" % sum(event_counts.values())
    return ret


def event_count_summary(daily_data_dict):
    """Returns a count of how many times each event level was detected."""
    ret = ""
    level_counts = dict()
    for day in daily_data_dict.keys():
        for event in daily_data_dict[day]['usability_events']:
            if daily_data_dict[day]['usability_events'][event]['worst_problem'] in level_counts:
                level_counts[daily_data_dict[day]['usability_events'][event]['worst_problem']] += 1
            else:
                level_counts[daily_data_dict[day]['usability_events'][event]['worst_problem']] = 1
    for level in sorted(level_counts.keys()):
        ret += "Level %s usability problems: %d\n" % (level, level_counts[level])
    return ret


def monthly_summary(daily_data_dict):
    """Produces a markdown fragment containing the summary of monthly data.
    DAILY_DATA_DICT is of course the dictionary of pickled data that was assumbled
    by produce_monthly_report().
    """
    total_transmitted = sum([item['packets_transmitted_today'] for item in daily_data_dict.values()])
    total_received = sum([item['packets_received_today'] for item in daily_data_dict.values()])
    ret = """For this month, network-reporter has data for %d days: %s.

During this time, network-reporter transmitted %d and received %d packets. That's an overall packet loss rate of %.3f %%.


## Summary of tests failed:

%s

## Count of usability events by level:

%s
"""
    ret = ret % (
        len(daily_data_dict), ', '.join(sorted([os.path.basename(item).strip().rstrip('.pkl') for item in daily_data_dict.keys()])),
        total_transmitted, total_received, 100 * ((total_transmitted - total_received)/total_transmitted),
        tests_failed_list(daily_data_dict),
        event_count_summary(daily_data_dict),
    )
    return ret


def daily_links(daily_data_dict):
    """Returns links to the reports for individual days during the month."""
    olddir = os.getcwd()
    try:
        year, month, _ = os.path.basename(list(daily_data_dict.keys())[0]).rstrip('.pkl').split('-')       # More than a little hacky.
        os.chdir(os.path.join(reports_location, year, month))
        ret = ""
        for date in sorted(daily_data_dict.keys()):
            key = os.path.basename(date).strip().rstrip('.pkl')
            ret += "%s: [<code>ping</code>](%s)\n" % (key, key + ".md")
            if os.path.isfile(key + "-traceroute.md"):
                ret += ", [<code>traceroute</code>(%s)" % (key + "-traceroute.md",)
        return ret
    finally:
        os.chdir(olddir)


def produce_monthly_report(datafile_directory):
    """Produces a markdown report summarizing the month's activity. Stores it in the
    appropriate part of the local filesystem. DATAFILE_DIRECTORY is of course the
    directory in which the datafiles are stored.
    """
    daily_data = {}.copy()                      # All of the un-pickled daily report data, by date.
    for datafile in glob.glob(os.path.join(datafile_directory, '*pkl')):
        with open(datafile, mode="rb") as data_store:
            daily_data[datafile] = pickle.load(data_store)
    # date on which data was collected; overall summary; usability problem log, description of ping rules
    year, month, _ = os.path.basename(list(daily_data.keys())[0]).rstrip('.pkl').split('-')  # More than a little hacky.
    report = monthly_report_template() % (situation,
                                          year + '-' + month,
                                          monthly_summary(daily_data),
                                          daily_links(daily_data),
                                          )
    report_loc = os.path.join(reports_location, year, month, "Monthly Summary.md")
    os.makedirs(os.path.dirname(report_loc), exist_ok=True)     # Ensure report directory exists
    with open(report_loc, mode="w") as output_file:
        output_file.write(report)

def daily_report_template():
    """Returns a markdown template for the daily reports. This template will include
    percent-codes for information to be filled in by the calling function.
    """
    ret = """
# Network Quality Report for %s

%s

## Usability problem log

%s

## Traceroute data

%s

## Tests applied to ping transcripts

%s
"""  # Substitute in: date on which data was collected; overall summary; usability problem log, traceroute verbiage, description of ping rules
    return ret

def daily_summary(data):
    """Returns an overall summary for the day's performance."""
    trans, rec = data['packets_transmitted_today'], data['packets_received_today']
    all_pings = [][:]
    for i in data['ping_transcripts']:
        if 'log' in data['ping_transcripts'][i]:
            for n in data['ping_transcripts'][i]['log']:
                try:
                    all_pings += [ float(n['time']) ]
                except KeyError:
                    pass            # If we didn't record it, don't count it toward the average calculation. Probably there was a DNS lookup failure or such.
    drop_pct = 100 * ((trans-rec)/trans) if (trans > 0) else 0
    return """Today, <code>network-monitor</code> transmitted %d and received %d packets; that's an overall packet loss rate of %.4f%%. As of the end of data recording on that day, the test interval was %d minutes and each test attempted to transmit %d packets.

### Overall statistics for all ping tests:

<dl>
<dt>min</dt><dd>%.4f</dd>
<dt>avg</dt><dd>%.4f</dd>
<dt>max</dt><dd>%.4f</dd>
<dt>std dev</dt><dd>%.4f</dd>
</dl>
""" % (trans, rec, drop_pct, interval_between_pings, number_of_packets,
       min(all_pings) if (len(all_pings) > 0) else 0,
       sum(all_pings)/len(all_pings) if (len(all_pings) > 0) else 0,
       max(all_pings) if (len(all_pings) > 0) else 0,
       statistics.stdev(all_pings) if (len(all_pings) > 0) else 0,
    )

def problem_log(data):
    """Returns a markdown fragment detailing the usability events logged in DATA."""
    probs = dict()
    for p_level in range(2,6):
        probs[p_level] = [dict(i) for i in data['usability_events'].values() if i['worst_problem'] == p_level]

    ret = """There were %d network usability events:

* %d events at level 2
* %d events at level 3
* %d events at level 4
* %d events at level 5

### Entire log

Here follows a list of all logged problems. Note that failures to log are not reported; currently,
there are several known reasons why logging fails occasionally. Even worse, the only way to detect these problems at
present is to inspect the raw (binary) log files by reading them with the <code>pickle</code> module in Python 3.5+.
Too, logging often begins and ends abruptly because development is still occurring. This also means that the exact
data format written to the raw files still changes occasionally.

All of this is to say that this log file is still documenting an experimental system; part of the aim of this
particular log file that you are reading right now is to help increase the stability of that system. The above
disclaimers will gradually disappear or be rewritten as the system approaches a more finalized form.
""" % (len(data['usability_events']), len(probs[2]), len(probs[3]), len(probs[4]), len(probs[5]))
    if 'usability_events' in data:
        ret += "\n<ul>\n"
        for timestamp, event_data in data['usability_events'].items():
            ret += "<li><strong>%s</strong> (problem level %d):\n <ul>\n" % (timestamp, event_data['worst_problem'])
            try:
                for test in event_data['tests_failed']:
                    ret += "  <li>Failed test: %s (%s)</li>\n" % (test['test_failed'], "; ".join(["%s=%s" % (label, value) for label, value in test['relevant_data'].items()]))
            except BaseException:
                log_it("WARNING: apparently, no tests were failed here. What's going on?", 1)
            ret += " </ul>\n</li>\n"
        ret += "</ul>"
    return ret

def single_rule_description(test):
    """Given a TEST (a bit of executable code run over a ping transcript), return
    the source description of the test. Rather fragile and based on the facts
    of how I'm currently writing tests for this program.
    """
    return inspect.getsourcelines(test)[0][0].strip().lstrip(""""'test': """).rstrip(',"').strip()

def ping_rules_description():
    """Returns a description of the rules currently used to check ping transcripts."""
    ret = "<ul>\n%s\n</ul>" % '\n'.join([' <li>%s (level %s): <i><code>%s</code></i>.</li>' % (i['test_name'], i['problem_level'], single_rule_description(i['test'])) for i in usability_tests])
    ret += "\nAnother rule that is always applied: if <code>ping</code> fails with a DNS lookup failure (or for any other reason), this is considered to be a **level 5** usability event."
    return ret

def traceroute_report(data, date):
    """Generates a report for any traceroute logs that were collected during the day.
    These logs are generated when a network usability event is detected and are
    dumped into a separate file. If any traceroute reports are generated, this
    function returns the filesystem path to the dumped report; otherwise it returns
    None.
    """
    if 'traceroute_transcripts' in data:
        report = """#Traceroute Report for""" + date + '\n\n'
        for e in data['traceroute_transcripts']:
            report += "##%s\n\n" % e
            report += "<p><pre><samp>" + data['traceroute_transcripts'][e]['transcript'] + "</samp></pre></p>\n\n"
        report_path = os.path.join(reports_location, datetime.datetime.now().strftime('%Y/%m'), date + "-traceroute.md")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)     # Ensure report directory exists
        with open(report_path, mode="w") as report_file:
            report_file.write(report)
        return report_path
    return None

def traceroute_verbiage(datafile, data):
    traceroute_path = traceroute_report(data, os.path.basename(datafile).rstrip('.pkl'))
    if traceroute_path:
        return """<a href="%s">Traceroute logs</a> were generated for this date.\n\n""" % traceroute_path
    else:
        return """No traceroute data was collected for this date. It could be that there were no network problems on this date, or it's possible that network-reporter is malfunctioning, or maybe this report is being generated from a datafile that was created before traceroute logging began.\n\n"""


def produce_daily_report(datafile):
    """Produces a markdown report summarizing the day's activity. Stores it in the
    appropriate part of the local filesystem.
    """
    with open(datafile, mode="rb") as data_store:
        daily_data = pickle.load(data_store)
    # date on which data was collected; overall summary; usability problem log, description of ping rules
    report = daily_report_template() % (os.path.basename(datafile).rstrip('.pkl'),
                                        daily_summary(daily_data),
                                        problem_log(daily_data),
                                        traceroute_verbiage(datafile, daily_data),
                                        ping_rules_description(),
                                       )
    report_loc = os.path.join(reports_location, datetime.datetime.now().strftime('%Y/%m'), os.path.basename(datafile).rstrip('.pkl')+'.md')
    os.makedirs(os.path.dirname(report_loc), exist_ok=True)     # Ensure report directory exists
    with open(report_loc, mode="w") as output_file:
        output_file.write(report)


if __name__ == "__main__":
    if False:               # Previous tests and routine work
        for d in glob.glob("""/home/patrick/Documents/programming/python_projects/network-reporter/data/2017/12/*pkl"""):
            produce_daily_report(d)
    if False:
        most_recent_report = sorted(glob.glob(os.path.join(data_location, "*pkl")))[-1]
    if True:
        produce_monthly_report("/home/patrick/torrents/FourMileFlats internet/2017/12/data")
