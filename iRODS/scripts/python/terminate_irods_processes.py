from __future__ import print_function
import subprocess
import os
import sys
import psutil

#
# This script finds iRODS processes owned by the current user,
# confirms their full_path against this installation of iRODS,
# checks their executing state, then pauses and kills each one.
#

def get_pids_executing_binary_file(binary_file_path):
    # get lsof listing of pids
    p = subprocess.Popen(['lsof', '-F', 'pf', binary_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
    out, err = p.communicate()
    out = out.decode() if p.returncode == 0 else ''
    parsed_out = parse_formatted_lsof_output(out)
    try:
        # we only want pids in executing state
        return [int(d['p']) for d in parsed_out if d['f'] == 'txt']
    except (ValueError, KeyError):
        raise IrodsControllerError('\n\t'.join([
            'non-conforming lsof output:',
            '{0}'.format(out),
            '{0}'.format(err)]),
            sys.exc_info()[2])

def parse_formatted_lsof_output(output):
    parsed_output = []
    if output.strip():
        for line in output.split():
            if line[0] == output[0]:
                parsed_output.append({})
            parsed_output[-1][line[0]] = line[1:]
    return parsed_output

top_level_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
for binary in ["irodsServer", "irodsReServer", "irodsXmsgServer", "irodsAgent"]:
    full_path = os.path.join(top_level_dir, "iRODS/server/bin/"+binary)
    for pid in get_pids_executing_binary_file(full_path):
        #print("killing %d %s" % (pid, full_path))
        p = psutil.Process(pid)
        p.suspend()
        p.terminate()
        p.kill()
