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

import collections, datetime, os, pickle, subprocess, _thread, time
from collections import OrderedDict

from config import *        # Constants defining program operation.
import reporter             # part of this same package

import patrick_logger       # https://github.com/patrick-brian-mooney/python-personal-library
from patrick_logger import log_it


patrick_logger.verbosity_level = 5

# This next group of functions handles storing and retrieving data for today's network tests.
# This is actually an inefficient way to do this, but it'll work for the simple tasks this program needs, since there shouldn't
# be concurrent multiple attempts to read from or write to the data store.
def _current_date():
    """Convenience function: return the current date in a canonical format, to be used
    in a filename.
    """
    return datetime.datetime.now().strftime ("%Y-%m-%d")

def current_data_store_name():
    """Convenience function: return the name of the data store we're supposed to be
    currently using.
    """
    return os.path.join(data_location, _current_date() + ".pkl")

def current_timestamp():
    return datetime.datetime.now().time().strftime('%H:%M:%S')

def get_ping_version():
    """Ask the PING executable what its version is."""
    return subprocess.check_output('%s %s' % (ping_exec, ping_version_flag), shell=True).decode().strip()

def create_data_store():
    """Create a new data store for the current day. This should only be called when
    there is no existing data store for the current date; if it's ever called when
    that's not the case, it will happily overwrite the existing data store with a
    new blank one.
    """
    default_data = collections.OrderedDict({'purpose of this file': 'data store for network test at %s on %s' % (situation, _current_date()),
                                            'script URL': 'https://github.com/patrick-brian-mooney/network-reporter',
                                            'script author twitter ID': '@patrick_mooney',
                                            'packets transmitted today': 0,
                                            'packets received today': 0,
                                            'ping transcripts': OrderedDict({}),
                                            'usability_events': OrderedDict({}),
                                            'ping version': get_ping_version(),
                                            })
    with open(current_data_store_name(), 'wb') as the_data_file:
        pickle.dump(default_data, file=the_data_file, protocol=-1)

def get_data_store(second_try=False):
    """Private function to get the entire stored data dictionary. If the data
    storage dictionary cannot be read, create a new dictionary with default
    values.

    Returns a dictionary containing all of the global stored data.
    """
    try:
        with open(current_data_store_name(), 'rb') as the_data_file:
            return pickle.load(the_data_file)
    except Exception:
        if second_try:
            log_it("FATAL ERROR: unable to create a readable data store; quitting ...", 0)
            os.exit()
        else:
            log_it('WARNING: Data store does not exist or cannot be read; creating new data store ...')
            create_data_store()
            return get_data_store(second_try=True)

def add_data_entry(category, time, data):
    """The per-day data store contains several (currently, two) information logs. This
    function adds an entry to one of those logs.

    CATEGORY is the key name in the global data store that stores an event log;
        currently, valid choices are 'ping transcripts' and 'usability_events'.
    TIME is the time the event is logged. This is the key name used to index the
        dictionary stored in the CATEGORY specified.
    DATA is the data to store for the event. Each CATEGORY has its own DATA format:

    Returns NONE.
    """
    daily_data = get_data_store()
    daily_data[category][time] = data
    if category == 'ping transcripts':
        daily_data['packets transmitted today'] += int(data['packets transmitted'])
        daily_data['packets received today'] += int(data['received'])
    with open(current_data_store_name(), 'wb') as the_data_file:
        pickle.dump(daily_data, file=the_data_file, protocol=-1)

def check_ping_config():
    """Verify that the user-supplied PING configuration results in a useful executable
    command.
    """
    def report_ping_error(exit_code=0, error=None, ping_transcript=""):
        log_it("WARNING: unable to validate ping configuration.", 0)
        if exit_code: log_it("       The return code was: %s" % exit_code, 0)
        if error: log_it("       The system complained: %s" % error, 0)
        log_it("       Please check the ping configuration at the top of reporter.py", 0)
        if ping_transcript:log_it("\n\n       Transcript of interaction with PING executable:\n\n%s" % ping_transcript, 2)

    log_it("INFO: testing ping configuration", 3)
    try:
        ping_command = "%s %s %s" % (ping_exec, ping_count_flag % 1, ping_target)
        status, result = subprocess.getstatusoutput(ping_command)
        log_it("INFO: successfully ran the test ping command `%s`" % ping_command, 3)
    except BaseException as e:
        report_ping_error(error=e)

def startup():
    """Execute necessary startup tasks."""
    check_ping_config()
    log_it("INFO: startup tasks complete", 3)

def interpret(data, timestamp):
    """Takes the DATA that record_and_interpret() collects and judges whether it
    describes a usable connection. Logs a usability event if it determines that
    usability is below acceptable levels.
    """
    failed_test_data = collections.OrderedDict({'worst_problem': 0, 'tests_failed': [][:]})
    for test in reporter.usability_tests:
        if test['test'](data):          # Tests return True if they fail, i.e. if there's a usability problem
            current_failure = collections.OrderedDict({'test_failed': test['test_name']})  # So log the event and its relevant data
            current_failure['relevant_data'] = {}.copy()
            current_failure['problem_level'] = test['problem_level']
            current_failure['test_group'] = test['test_group']
            for key in test['data_keys_to_report']:
                current_failure['relevant_data'][key] = data[key]
            failed_test_data['worst_problem'] = max(failed_test_data['worst_problem'], test['problem_level'])
            failed_test_data['tests_failed'] += [ current_failure ]
    try:
        if failed_test_data['worst_problem'] >= 2:          # We only log usability problem events when they impact use.
            # First, prune the data so only the worst experienced version of each problem category remains

            # Now, add the entry
            add_data_entry('usability_events', timestamp, failed_test_data)
    except KeyError:
        pass            # Didn't fail ANY tests? move along.

def record_and_interpret(timestamp, ping_transcript):
    """Read through the transcript. Break it down and record it, and then evaluate it.
    If necessary, log a usability event.

    Note that this is currently heavily dependent on the format of the output produced
    by the PING command. For reference, this script was developed with Linux ping
    included with iputils-s20121221.
    """
    data = dict([])
    log_it("INFO: we're recording a ping transcript from %s" % timestamp, 2)
    log_it("      transcript follows:\n\n%s\n\n" % ping_transcript, 3)
    lines = ping_transcript.strip().split('\n')
    header = lines.pop(0).rstrip('bytes of data.')          # Read the first line in the ping_transcript
    # Current format is: PING google.com (172.217.1.206) 56(84) bytes of data.
    data['executable name'], data['hostname'], data['host IP'], data['bytes'] = header.strip().split(' ')
    # Next, gather data from the last line from the file
    trailer = lines.pop().lstrip('rtt').strip()
    label, trailer = trailer.split('=')
    if ',' in trailer:
        stats, data['pipe num'] = trailer.split(',')
    else:
        stats = trailer.strip()
    data.update(dict(zip(label.strip().split('/'), stats.strip().split('/'))))
    # Now, gather data from the last remaining line that hasn't already been processed
    trailer = lines.pop().strip()
    data['packets transmitted'], trailer = trailer.split('packets transmitted,')
    data['received'], trailer = trailer.split(' received,')
    data['packet loss'], trailer = trailer.split('packet loss,')
    data['time'] = trailer.split('time')[1]
    # The last remaining line is purely for display: pop it and ignore it
    _ = lines.pop()
    # Streamline the rest of the ping_transcript, then process it line by line
    lines = [ l.strip()+'\n' for l in lines if len(l.strip()) > 0 and not l.strip().startswith('---') ]
    data['log'] = [][:]
    for l in lines:
        event=dict([])
        the_line = l[:]
        data['return packet size'], the_line = the_line.strip().split('bytes from')
        data['host ID (reverse DNS)'], the_line = the_line.split('(')
        _, the_line = the_line.split(':')               # Drop the IP address, which we've already seen anyway.`
        icmp, ttl, time, _ = the_line.strip().split(' ')
        event['icmp_seq'] = icmp.split('=')[1].strip()
        data['ttl'] = ttl.split('=')[1].strip()
        event['time'] = time.split('=')[1].strip()
        data['log'] += [event]
    for k in data:                              # Clean up leading and trailing whitespace in the data.
        if type(data[k]) == type('string'):
            data[k] = data[k].strip()
    add_data_entry('ping transcripts', timestamp, data)
    interpret(data, timestamp)

def ping_test():
    """Use PING to run a network test. Returns the command's output for interpretation.
    """
    status, output = subprocess.getstatusoutput("%s %s %s" % (ping_exec, ping_count_flag % number_of_packets, ping_target))
    if status:      # Non-zero exit code means we couldn't ping. Log it as a serious error.
        failure_data = OrderedDict({'worst_problem': 5 })
        failure_data['tests_failed'] = [ {'test_failed': 'PING returned non-zero exit status' }, ]
        failure_data['tests_failed'][0]['relevant_data'] = {'status_code': status, 'output': output}
        failure_data['tests_failed'][0]['problem_level'] = 5
        failure_data['tests_failed'][0]['test_group'] = 'ping failure'
        add_data_entry('usability_events', current_timestamp(), failure_data)
    return output

def schedule_test(delay=0):
    """Waits DELAY seconds; then, runs a test, interprets it, and stores the results.
    """
    log_it("INFO: scheduling next ping test for %d seconds from now" % delay, 3)
    time.sleep(delay)
    log_it("INFO: beginning ping test ...", 1)
    timestamp = current_timestamp()
    transcript = ping_test()
    log_it("INFO: ping test complete, interpreting ...", 2)
    record_and_interpret(timestamp, transcript)

def monitor():
    """Intermittently schedule a test, run it, interpret it, and log the results."""
    log_it("INFO: beginning monitoring", 3)
    while True:
        current_time = datetime.datetime.now()
        next_run = current_time + datetime.timedelta(minutes=interval_between_pings)    # Add interval_between_pings to current time ...
        next_run = datetime.datetime(next_run.year, next_run.month, next_run.day, next_run.hour, next_run.minute // interval_between_pings * interval_between_pings, 0)    # ... and round down
        log_it("INFO: it's %s; scheduling next ping test for %s" % (current_time.isoformat(sep=' '), next_run.isoformat(sep=' ')), 3)
        sleep_time = (next_run - current_time).total_seconds()
        _thread.start_new_thread(schedule_test, (sleep_time,))
        time.sleep(1 + sleep_time)

if __name__ == "__main__":
    log_it("INFO: beginning run ...", 3)
    startup()
    monitor()
    log_it("INFO: program reached normal termination", 5)
