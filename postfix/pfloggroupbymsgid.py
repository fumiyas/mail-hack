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
    rb'(?P<timestamp>\d{4}-[0-1]\d-[0-3]\dT[0-1]\d:[0-5]\d:[0-5]\d(\.\d+)?[-+][0-1]\d:[0-5]\d|[A-Z][a-z][a-z] [ 1-3]\d [0-1]\d:[0-5]\d:[0-5]\d) '
    rb'(?P<hostname>[-.\d\w]+) '
    rb'postfix/(?:(?P<service_prefix>[-.\d\w]+/)?(?P<service>[-.\d\w]+))\[(?P<pid>\d+)\]: '
    rb'(?:(?P<qid>[0-9A-F]{6,}|[0-9B-DF-HJ-NP-TV-Zb-df-hj-np-tv-y]{10,}z[0-9B-DF-HJ-NP-TV-Zb-df-hj-np-tv-y]+): )(?P<content_raw>.*)$',
    re.ASCII
)
log_cleanup_msgid_re = re.compile(
    r'^message-id=(?P<msgid><.*>)$',
    re.ASCII
)
log_cleanup_filter_re = re.compile(
    r'^(?P<action>info|hold|reject|discard): '
    r'(?P<targeted>header (?P<header>.*)) '
    r'(?P<proto>from [-.\d\w]+\[[\da-f.:]+\]; from=<.*?> to=<.*?> proto=\S+ helo=<.*?>)'
    r'(: (?P<message>.*))?$',
    re.ASCII
)

padding = " " * 24

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

    ## Remove decimal point and time zone
    log["timestamp"] = re.sub(r"\..+$", "", log["timestamp"])

    try:
        log["content"] = m["content_raw"].decode()
    except UnicodeDecodeError:
        log["content"] = f"{m['content_raw']!r}"
    qid = log["qid"]

    logs_by_qid.setdefault(qid, []).append(log)

    if log['service'] == 'cleanup':
        m = log_cleanup_msgid_re.match(log['content'])
        if m:
            msgid_by_qid[qid] = m['msgid']
        m = log_cleanup_filter_re.match(log['content'])
        if m:
            action = m['action'].upper() if m['action'] != 'info' else m['action']
            log['content'] = f"{action}: {m['targeted']}\n{padding}{m['proto']}"
            if m['message']:
                log['content'] += f"\n{padding}{m['message']}"
    if log['service'] in ('local', 'smtp'):
        log["content"] = re.sub(r", (status=)", f"\n{padding}\\1", log["content"])
    elif log['service'] == 'qmgr' and log['content'] == 'removed':
        if qid in msgid_by_qid:
            msgid = msgid_by_qid[qid]
        else:
            msgid_unknown_count += 1
            msgid = f"UNKNOWN-MESSAGE-ID-{msgid_unknown_count}"
        logs = logs_by_qid.pop(qid)
        if not msgids or msgid in msgids:
            logs_list_by_msgid.setdefault(msgid, []).append(logs)

for qid, logs in logs_by_qid.items():
    msgid = msgid_by_qid.get(qid)
    if msgid is None:
        msgid_unknown_count += 1
        msgid = f"UNKNOWN-MESSAGE-ID-{msgid_unknown_count}"
    logs_list_by_msgid[msgid] = [logs]

## FIXME: Print pending queue logs
for msgid, logs_list in logs_list_by_msgid.items():
    print(f"Message-ID: {msgid}")
    for logs in logs_list:
        print(f"  Queue ID: {logs[0]['qid']}")
        for log in logs:
            print(f"    {log['timestamp']} {log['service']} {log['content']}")
