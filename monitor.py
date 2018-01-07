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
    return datetime.datetime.now().strftime('%Y/%m/%Y-%m-%d')

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

def create_data_store(which_store=None):
    """Create a new data store for the specified day. This should only be called when
    there is no existing data store for the current date; if it's ever called when
    that's not the case, it will happily overwrite the existing data store with a
    new blank one.
    """
    if which_store == None:
        which_store = current_data_store_name()
    default_data = collections.OrderedDict({'purpose of this file': 'data store for network test at %s on %s' % (situation, _current_date()),
                                            'script URL': 'https://github.com/patrick-brian-mooney/network-reporter',
                                            'script author twitter ID': '@patrick_mooney',
                                            'packets_transmitted_today': 0,
                                            'packets_received_today': 0,
                                            'ping_transcripts': OrderedDict(),
                                            'traceroute_transcripts': OrderedDict(),
                                            'usability_events': OrderedDict(),
                                            'ping version': get_ping_version(),
                                            })
    with open(which_store, 'wb') as the_data_file:
        pickle.dump(default_data, file=the_data_file, protocol=-1)

def get_data_store(which_store=None, second_try=False):
    """Private function to get an entire stored data dictionary. If the data
    storage dictionary cannot be read, create a new dictionary with default
    values. If WHICH_STORE is None, then it returns data from the current data
    store; otherwise, it returns the data from the store specified by WHICH_STORE.

    Returns a dictionary containing all of the stored data from the specified
    data store.
    """
    if which_store == None:
        which_store = current_data_store_name()
    try:
        with open(which_store, 'rb') as the_data_file:
            return pickle.load(the_data_file)
    except Exception as e:
        if second_try:
            log_it("FATAL ERROR: unable to create a readable data store; quitting ...", 0)
            os.exit()
        else:
            log_it('WARNING: Data store does not exist or cannot be read (the system said: %s); creating new data store ...' % e)
            create_data_store()
            return get_data_store(second_try=True)

def add_data_entry(category, time, data):
    """The per-day data store contains several (currently, two) information logs. This
    function adds an entry to one of those logs.

    CATEGORY is the key name in the global data store that stores an event log;
        valid choices are specified below.
    TIME is the time the event is logged. This is the key name used to index the
        dictionary stored in the CATEGORY specified.
    DATA is the data to store for the event. Each CATEGORY has its own DATA format:

    Returns NONE.
    """
    valid_categories = ['ping_transcripts', 'traceroute_transcripts', 'usability_events']
    assert data, "ERROR: record_data_entry(): attempt to store blank data in category %s" % category
    assert category in valid_categories, "ERROR: attempt to add data to unknown category %s" % category
    daily_data = get_data_store()
    if category not in daily_data:
        daily_data[category] = OrderedDict()
    daily_data[category][time] = data

    # Handling for special-casing of monitored and calculated values happens below.
    if category == 'ping_transcripts':
        try:
            daily_data['packets_transmitted_today'] += int(data['packets_transmitted'])
        except KeyError: pass
        try:
            daily_data['packets_received_today'] += int(data['received'])
        except KeyError: pass
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

def record_traceroute():
    """Record a traceroute transcript in the log."""
    status, output = subprocess.getstatusoutput("%s %s" % (traceroute_exec, ping_target))
    add_data_entry('traceroute_transcripts', current_timestamp(), {'status': status, 'transcript': output})

def schedule_report_creation(data_file):
    """Schedule the postprocessing of a data file. Since data files are for particular
    days, this postprocessing should happen a few minutes after midnight. When it
    runs, it waits for the data file to stop changing, then produces a report for
    that data file. This procedure is intended to be started as a thread.
    
    #FIXME: makes a number of assumptions about timing that should be checked and
    might need to be adjusted.
    """
    s = datetime.datetime.replace(datetime.datetime.now() + datetime.timedelta(days=1), hour=0, minute=10, second=0) - datetime.datetime.now()
    time.sleep(s.seconds)           # Sleep until 12:10 a.m.
    old_time, new_time = 0, os.stat(data_file).st_mtime
    while old_time != new_time:     # Wait until it's unchanged for five minutes
        time.sleep(300)
        old_time, new_time = new_time, os.stat(filename).st_mtime
    reporter.produce_daily_report(data_file)
    # Great! We've produced the report for yesterday's data. Let's schedule the reporting of today's data for tomorrow before the thread terminates. 
    _thread.start_new_thread(schedule_report_creation, (current_data_store_name(),))
    
def startup():
    """Execute necessary startup tasks."""
    check_ping_config()
    _thread.start_new_thread(schedule_report_creation, (current_data_store_name(),))
    log_it("INFO: startup tasks complete", 3)

def interpret(data, timestamp):
    """Takes the DATA that record_and_interpret() collects and judges whether it
    describes a usable connection. Logs a usability event if it determines that
    usability is below acceptable levels.
    """
    failed_test_data = collections.OrderedDict({'worst_problem': 0, 'tests_failed': [][:]})
    for test in reporter.usability_tests:
        try:
            result = test['test'](data)
        except BaseException:
            result = False                  # If we can't even run the test, a usability problem has already been reported
        if result:          # Tests return True if they fail, i.e. if there's a usability problem
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
            pruned_data = [][:]
            groups_failed = set([ i['test_group'] for i in failed_test_data['tests_failed'] ])
            for problem in groups_failed:
                worst_version = max([ test['problem_level'] for test in failed_test_data['tests_failed'] if test['test_group']==problem])
                pruned_data += [f for f in failed_test_data['tests_failed'] if (f['test_group'] == problem and f['problem_level'] == worst_version)]
            failed_test_data['tests_failed'] = pruned_data
            # Now, add the entry
            add_data_entry('usability_events', timestamp, failed_test_data)
            # add_data_entry('usability_events', timestamp, pruned_data)
            record_traceroute()
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
    t = ping_transcript.lower()
    if "failure in name" in t or "net unreachable" in t:
        data['transcript'] = ping_transcript
    else:
        lines = ping_transcript.strip().split('\n')
        header = lines.pop(0).rstrip('bytes of data.')          # Read the first line in the ping_transcript
        # Current format is: PING google.com (172.217.1.206) 56(84) bytes of data.
        data['executable_name'], data['hostname'], data['host_IP'], data['bytes'] = header.strip().split(' ')
        # Next, gather data from the last line from the file
        trailer = lines.pop().lstrip('rtt').strip()
        label, trailer = trailer.split('=')
        if ',' in trailer:
            stats, data['pipe_num'] = trailer.split(',')
        else:
            stats = trailer.strip()
        data.update(dict(zip(label.strip().split('/'), stats.strip().split('/'))))
        # Now, gather data from the last remaining line that hasn't already been processed
        trailer = lines.pop().strip()
        errors_pos = trailer.find("errors")
        if errors_pos != -1:
            log_it("WARNING: network errors detected; we may be about to crash")
        data['packets_transmitted'], trailer = trailer.split('packets transmitted,')
        data['received'], trailer = trailer.split(' received,')
        if trailer.strip().startswith('+') and "errors" in trailer:
            errors, trailer = trailer.split('errors, ')
            data['errors'] = errors.strip().lstrip('+').strip()
        data['packet_loss'], trailer = trailer.split('packet loss,')
        data['time'] = trailer.split('time')[1]
        # The last remaining line is purely cosmetic: pop it and ignore it
        _ = lines.pop()
        # Streamline the rest of the ping_transcript, then process it line by line
        lines = [ l.strip()+'\n' for l in lines if len(l.strip()) > 0 and not l.strip().startswith('---') ]
        data['log'] = [][:]
        for l in lines:
            event=dict([])
            the_line = l[:]
            if "net unreachable" in the_line:
                event = {'icmp_seq': 1 + len(data['log']), 'transcript': the_line}
            else:
                try:
                    data['return_packet_size'], the_line = the_line.strip().split('bytes from')
                    data['host ID (reverse DNS?)'], the_line = the_line.split('(')
                    _, the_line = the_line.split(':')               # Drop the IP address, which we've already seen anyway.`
                    icmp, ttl, time, _ = the_line.strip().split(' ')
                    event['icmp_seq'] = icmp.split('=')[1].strip()
                    data['ttl'] = ttl.split('=')[1].strip()
                    event['time'] = time.split('=')[1].strip()
                except BaseException as e:
                    log_it("WARNING: unable to parse the ping transcript line: %s; halting instead of trying to parse the phrase: %s" % (l, the_line))
                    event = {'icmp_seq': 1 + len(data['log']), 'transcript': the_line}
            data['log'] += [event]
    for k in data:                              # Clean up leading and trailing whitespace in the data.
        if type(data[k]) == type('string'):
            data[k] = data[k].strip()
    add_data_entry('ping_transcripts', timestamp, data)
    interpret(data, timestamp)

def ping_test():
    """Use PING to run a network test. Returns the command's output for interpretation.
    """
    status, output = subprocess.getstatusoutput("%s %s %s" % (ping_exec, ping_count_flag % number_of_packets, ping_target))
    if status:      # Non-zero exit code means we couldn't ping. Log it as a serious error.
        failure_data = OrderedDict({'worst_problem': 5 })
        failure_data['tests_failed'] = [ {'test_failed': 'PING returned non-zero exit status',
                                          'relevant_data': {'status_code': status},
                                          'problem_level': 5,
                                          'test_group': 'ping failure' }, ]
        if len(output) <= 512:
            failure_data['tests_failed'][0]['relevant_data']['transcript'] = output
        add_data_entry('usability_events', current_timestamp(), failure_data)
    return output

def schedule_test(delay=0):
    """Waits DELAY seconds; then, runs a test, interprets it, and stores the results.
    """
    log_it("INFO: scheduling next ping test for %.3f seconds from now" % delay, 3)
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
