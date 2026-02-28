#!/usr/bin/env python3
## -*- coding: utf-8 -*- vim:shiftwidth=4:expandtab:
##
## Postfix: Group Postfix log by Message-ID: header and queue ID
##
## SPDX-FileCopyrightText: 2018-2026 SATOH Fumiyasu @ OSSTech Corp., Japan
## SPDX-License-Identifier: GPL-3.0-or-later
##

import sys
import re
from collections import OrderedDict

c_reset = "\x1b[m"
c_red = "\x1b[31m"
c_green = "\x1b[32m"
c_yellow = "\x1b[33m"
c_blue = "\x1b[34m"
c_magenta = "\x1b[35m"
c_cyan = "\x1b[36m"
pad = " "

log_raw_re = re.compile(
    rb'^'
    rb'(?P<timestamp>\d{4}-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:[0-5]\d(\.\d+)?[-+][0-1]\d:[0-5]\d|[A-Z][a-z][a-z] [ 1-3]\d [0-2]\d:[0-5]\d:[0-5]\d) '
    rb'(?P<hostname>[-.\d\w]+) '
    rb'postfix(?:-(?P<instance_name>[-.\d\w]+))?/(?:(?P<service_prefix>[-.\d\w]+)/)?(?P<service>[-.\d\w]+)\[(?P<pid>\d+)\]: '
    rb'(?P<content_raw>.*)'
    rb'$',
    re.ASCII
)

qid_re = r'(?P<qid>[0-9A-F]{6,}|[0-9B-DF-HJ-NP-TV-Zb-df-hj-np-tv-y]{10,}z[0-9B-DF-HJ-NP-TV-Zb-df-hj-np-tv-y]+)'
log_q_re = re.compile(
    r'^'
    f"{qid_re}"
    ': (?P<content_raw>.*)'
    r'$',
    re.ASCII
)
log_q_warning_re = re.compile(
    r'^'
    ## FIXME: Handle `error`, `fatal` messages
    r'warning: '
    ## FIXME: No standard format :-(
    r'(open [a-z]+|[_a-z][_a-z0-9]+: remove) '
    f"{qid_re}"
    ,
    re.ASCII
)

log_cleanup_msgid_re = re.compile(
    r'^'
    r'message-id=(?P<msgid>[^\s]*)'
    r'$',
    re.ASCII
)
log_cleanup_filter_re = re.compile(
    r'^'
    r'(?P<action>info|hold|reject|discard): '
    r'(?P<targeted>header (?P<header>.*)) '
    r'(?P<client>from [-.\d\w]+\[[\da-f.:]+\]); (?P<from_to>from=<.*?> to=<.*?>) (?P<proto>proto=\S+ helo=<.*?>)'
    r'(: (?P<text>.*))?'
    r'$',
    re.ASCII
)

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

    ## Remove decimal point, fraction and time zone
    log["timestamp"] = re.sub(r"\..+$", "", log["timestamp"])

    try:
        log["content"] = m["content_raw"].decode()
    except UnicodeDecodeError:
        log["content"] = f"{m['content_raw']!r}"

    m = log_q_re.match(log["content"])
    if m:
        log["qid"] = m["qid"]
        log["content"] = m["content_raw"]
    else:
        m = log_q_warning_re.match(log["content"])
        if not m:
            continue  # FIXME: Warn?
        log["qid"] = m["qid"]
    qid = log["qid"]

    logs_by_qid.setdefault(qid, []).append(log)

    if log['service'] == 'cleanup':
        m = log_cleanup_msgid_re.match(log['content'])
        if m:
            msgid_by_qid[qid] = m['msgid']
            ## Remove the redundant `cleanup message-id=<...>` log
            logs_by_qid[qid].pop()
            continue
        m = log_cleanup_filter_re.match(log['content'])
        if m:
            if m['action'] in ('hold'):
                c = c_yellow
            elif m['action'] in ('reject', 'discard'):
                c = c_red
            else:
                c = ""
            log['content'] = f"{c}{m['action']}{c_reset}: {m['targeted']}"
            if m['text']:
                ## Optional text
                log['content'] += f"\n{pad:<9}text: {m['text']}"
            log['content'] += f"\n{pad:<9}{m['from_to']}\n{pad:<9}{m['client']} {m['proto']}"
    elif log['service'] in ('local', 'smtp'):
        log["content"] = re.sub(r", ((relay|status)=)", f"\n{pad:<9}\\1", log["content"])
    elif (
        (log['service'] == 'qmgr' and log['content'] == 'removed') or
        (log['service'] == 'postsuper' and log['content'] in ('requeued', 'removed', 'expired'))
    ):
        if qid in msgid_by_qid:
            msgid = msgid_by_qid.pop(qid)
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
    logs_list_by_msgid.setdefault(msgid, []).append(logs)

for msgid, logs_list in logs_list_by_msgid.items():
    print(f"{c_green}Message-ID: {msgid}")
    for logs in logs_list:
        qid = logs[0]['qid']
        if qid in logs_by_qid:
            s = 'Pending'
            c = c_red
        else:
            s = 'Finished'
            c = c_magenta
        print(f"  {c}Queue ID: {qid} ({s})")
        for log in logs:
            extra = ''
            if instance_name := log.get('instance_name'):
                extra += f"{instance_name}/"
            if service_prefix := log.get('service_prefix'):
                extra += f"{service_prefix}/"
            print(f"    {c_cyan}{log['timestamp']}{c_reset} {extra}{log['service']} {log['content']}")
