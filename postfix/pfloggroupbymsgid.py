#!/usr/bin/env python3
## -*- coding: utf-8 -*- vim:shiftwidth=4:expandtab:
##
## Postfix: Group Postfix log by Message-ID: header
##
## SPDX-FileCopyrightText: 2018-2024 SATOH Fumiyasu @ OSSTech Corp., Japan
## SPDX-License-Identifier: GPL-3.0-or-later
##

import sys
import re
from collections import OrderedDict

log_raw_re = re.compile(
    rb'^'
    rb'(?P<timestamp>[0-9]{4}-[0-1][0-9]-[0-3][0-9]T[0-1][0-9]:[0-5][0-9]:[0-5][0-9](\.[0-9]+)?[-+][0-1][0-9]:[0-5][0-9]|[A-Z][a-z][a-z] [ 1-3][0-9] [0-1][0-9]:[0-5][0-9]:[0-5][0-9]) '
    rb'(?P<hostname>[-._A-Za-z0-9]+) '
    rb'postfix/(?:(?P<service_prefix>[-._0-9a-z]+/)?(?P<service>[-._0-9a-z]+))\[(?P<pid>[0-9]+)\]: '
    rb'(?:(?P<qid>[0-9A-F]{6,}|[0-9B-DF-HJ-NP-TV-Zb-df-hj-np-tv-y]{10,}z[0-9B-DF-HJ-NP-TV-Zb-df-hj-np-tv-y]+): )(?P<content_raw>.*)$'
)
log_cleanup_msgid_re = re.compile(r'^message-id=(?P<msgid><.*?>)$')

logs_by_qid = {}
logs_list_by_msgid = OrderedDict()
msgid_by_qid = {}
msgid_unknown_count = 0

msgids = sys.argv[1:]

for line in sys.stdin.buffer:
    line = line.strip()
    m = log_raw_re.match(line)
    if not m:
        continue

    log = {
        k: (v.decode() if k != "content_raw" else v)
        for k, v in m.groupdict().items()
        if v is not None
    }
    log["line_raw"] = line
    try:
        log["content"] = m.group("content_raw").decode()
    except UnicodeDecodeError:
        log["content"] = f"{m.group('content_raw')!r}"
    qid = log["qid"]

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
            msgid = f"UNKNOWN-MESSAGE-ID-{msgid_unknown_count}"
        logs = logs_by_qid.pop(qid)
        if not msgids or msgid in msgids:
            logs_list_by_msgid.setdefault(msgid, []).append(logs)

## FIXME: Print pending queue logs
for msgid, logs_list in logs_list_by_msgid.items():
    print(f"Message-ID: {msgid}")
    for logs in logs_list:
        print(f"  Queue ID: {logs[0]['qid']}")
        for log in logs:
            print(f"    {log['timestamp']} {log['service']} {log['content']}")
