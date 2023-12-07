#!/usr/bin/env python3
## -*- coding: utf-8 -*- vim:shiftwidth=4:expandtab:
##
## Postfix: Group Postfix log by Message-ID
## Copyright (c) 2018 SATOH Fumiyasu @ OSS Technology Crop., Japan
##
## License: GNU General Public License version 3 or later
##

from __future__ import print_function

import sys
import re
from collections import OrderedDict

log_re = re.compile(
    r'^'
    r'(?P<timestamp>[0-9]{4}-[0-1][0-9]-[0-3][0-9]T[0-1][0-9]:[0-5][0-9]:[0-5][0-9](\.[0-9]+)?[-+][0-1][0-9]:[0-5][0-9]|[^A-Z][a-z][a-z] [ 1-3][0-9] [0-1][0-9]:[0-5][0-9]:[0-5][0-9]) '
    r'(?P<hostname>[-._A-Za-z0-9]+) '
    r'postfix/(?:(?P<service_prefix>[-._0-9a-z]+/)?(?P<service>[-._0-9a-z]+))\[(?P<pid>[0-9]+)\]: '
    r'(?:(?P<qid>[0-9A-F]{6,}|[0-9B-DF-HJ-NP-TV-Zb-df-hj-np-tv-y]{10,}z[0-9B-DF-HJ-NP-TV-Zb-df-hj-np-tv-y]+): )(?P<content>.*)$'
)
log_cleanup_msgid_re = re.compile(r'^message-id=<(?P<msgid>.*?)>$')

logs_by_qid = {}
logs_list_by_msgid = OrderedDict()
msgid_by_qid = {}
msgid_unknown_count = 0

msgids = sys.argv[1:]

for line in sys.stdin:
    line = line.strip()
    m = log_re.match(line)
    if not m:
        continue

    qid = m.group('qid')
    log = {
        'line': line,
        'timestamp': m.group('timestamp'),
        'pid': m.group('pid'),
        'qid': qid,
        'service_prefix': m.group('service_prefix'),
        'service': m.group('service'),
        'content': m.group('content'),
    }

    logs_by_qid.setdefault(qid, []).append(log)

    if log['service'] == 'cleanup':
        m = log_cleanup_msgid_re.match(log['content'])
        if m:
            msgid_by_qid[qid] = m.group('msgid')
    elif log['service'] == 'qmgr' and log['content'] == 'removed':
        if qid in msgid_by_qid:
            msgid = msgid_by_qid[qid]
        else:
            msgid_unknown_count += 1
            msgid = 'UNKNOWN-MESSAGE-ID-%d' % (msgid_unknown_count)
        logs = logs_by_qid.pop(qid)
        if not msgids or msgid in msgids:
            logs_list_by_msgid.setdefault(msgid, []).append(logs)

## FIXME: Print pending queue logs
for msgid, logs_list in logs_list_by_msgid.items():
    print(f"Message-ID: <{msgid}>")
    for logs in logs_list:
        print(f"  Queue ID: {logs[0]['qid']}")
        for log in logs:
            print(f"    {log['timestamp']} {log['service']} {log['content']}")
