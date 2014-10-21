#!/usr/bin/env python

"""Utility for producing a stack trace from a minidump.

This runs the minidump_stackwalk tool to extract a stacktrace
from a minidump and symbolize it.

The output of minidump_stackwalk is then parsed and the details
of the system where the crash occurred and stack trace of the
crashing thread are output.
"""

from __future__ import print_function

import argparse
import os
import subprocess
import sys

import minidump_stackwalk_processor

def run_stackwalk(minidump_tool, dump_file, symbol_fetch_command, verbose = False):
    stderr_output = subprocess.PIPE
    if verbose:
        stderr_output = sys.stderr

    proc = subprocess.Popen([minidump_tool, '-m', dump_file, '-e', symbol_fetch_command],
      stdout=subprocess.PIPE, stderr=stderr_output)
    stdout, stderr = proc.communicate()

    trace = minidump_stackwalk_processor.Stacktrace.parse(stdout)
    main_module = trace.modules[trace.main_module]
    version = main_module.version or 'Unknown version'

    print('App: %s (%s)' % (main_module.filename, version))
    print('Crash: %s in thread %s' % (trace.crash_info.type, trace.crash_info.thread_id))
    print('OS: %s %s' % (trace.os_version.platform, trace.os_version.build_id))
    print('\nStacktrace for thread %s:' % (trace.crash_info.thread_id)) 
    for frame in trace.threads[trace.crash_info.thread_id]:
        if frame.function:
            print('  %s' % frame.function)
        else:
            print('  [Unknown in %s]' % frame.module)

def main():
    parser = argparse.ArgumentParser(description="Produce a stack trace from a minidump")
    parser.add_argument('dump_file', action='store', type=str, help='Path to minidump file')
    parser.add_argument('-v', action='store_true', dest='verbose', help='Display verbose output from minidump_stackwalk')
    args = parser.parse_args()
    
    minidump_tool = os.environ.get('MINIDUMP_STACKWALK_PATH')
    if not minidump_tool:
        print("""MINIDUMP_STACKWALK_PATH not set. This should be set to the path of the
              minidump_stackwalk tool.""")
        sys.exit(1)

    sym_url = os.environ.get('MINIDUMP_STACKWALK_SYMBOL_URL')
    if not sym_url:
        print("""MINIDUMP_STACKWALK_SYMBOL_URL not set. This should be set to the URL
              where debug symbols are hosted.""")
        sys.exit(1)

    sym_fetch_tool = os.path.abspath(os.path.dirname(__file__) + '/fetch-symbols.py')
    sym_fetch_command = '%s -s \"%s\"' % (sym_fetch_tool, sym_url)

    run_stackwalk(minidump_tool, args.dump_file, sym_fetch_command, verbose=args.verbose)

if __name__ == '__main__':
    main()
