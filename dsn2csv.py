#!/usr/bin/env python
## -*- coding: utf-8 -*- vim:shiftwidth=4:expandtab:
##
## Parse a DSN message in a VERP-ed bounced message and dump to CSV data
## Copyright (c) 2018 SATOH Fumiyasu @ OSS Technology Co., Japan
##
## License: GNU General Public License version 3
##

from __future__ import print_function

import sys
import re
import time
import csv
import email.parser
import email.utils

RE_ADDR_VERP = re.compile(
    r'\A'
    r'(?P<local>(?P<local_base>[^+@]+)'
    r'\+'
    r'(?P<local_ext>(?P<bounce_local>[^=@]+)=(?P<bounce_domain>[^=@]+)))'
    r'@'
    r'(?P<domain>[^@]+)'
    r'\Z'
    )
RE_DSN_LINE = re.compile(r'^(?P<name>[^:]+): *(?P<value>.*)$')


def bounced_msg_in_msg(msg):
    if msg['return-path'] == '<>':
        return msg
    for msg_part in msg.walk():
        if msg_part['return-path'] == '<>':
            return msg_part
    return None

def bounced_to_in_msg(msg):
    for name in ('to', 'delivered-to'):
        addr_header = msg[name]
        addr = email.utils.parseaddr(addr_header)
        addr_verp_matched = RE_ADDR_VERP.search(addr[1])
        if addr_verp_matched:
            return \
                addr_verp_matched['bounce_local'] + \
                '@' + \
                addr_verp_matched['bounce_domain']
    return None


def dsn_msg_in_msg(msg):
    for msg_part in msg.walk():
        if msg_part.get_content_type() == 'message/delivery-status':
            return msg_part
    return None


def dsn_msg_parse(msg):
    dsn_info = {}
    for line in str(msg).split('\n'):
        m = RE_DSN_LINE.search(line)
        if m:
            dsn_info[m['name'].lower()] = m['value']
    return dsn_info


def main(argv):
    csv_writer = csv.writer(sys.stdout)
    csv_writer.writerow(('Address', 'Date', 'Status', 'Diagnostic-Code'))

    msg_parser = email.parser.Parser()
    bounced_info_by_addr = {}
    for msg_file in argv:
        with open(msg_file, 'r', encoding='UTF-8', errors='replace') as msg_f:
            try:
                msg = msg_parser.parse(msg_f)
            except UnicodeDecodeError as e:
                print('ERROR: %s: %s' % (msg_file, e), file=sys.stderr)
                continue

        msg_bounced = bounced_msg_in_msg(msg)
        if not msg_bounced:
            continue

        bounced_addr = bounced_to_in_msg(msg_bounced)
        if bounced_addr is None or bounced_addr in bounced_info_by_addr:
            continue

        dt_tuple = email.utils.parsedate(msg_bounced['date'])
        bounced_info = bounced_info_by_addr[bounced_addr] = {
            'address': bounced_addr,
            'date': time.strftime('%Y-%m-%d %H:%M:%S', dt_tuple),
            }

        dsn = dsn_msg_in_msg(msg_bounced)
        if dsn:
            bounced_info['dsn'] = dsn_msg_parse(dsn)
        else:
            bounced_info['dsn'] = {}

        csv_writer.writerow([
            bounced_info['address'],
            bounced_info['date'],
            bounced_info['dsn'].get('status'),
            bounced_info['dsn'].get('diagnostic-code'),
            ])

    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: %s FILENAME [...]" % (sys.argv[0]), file=sys.stderr)
        sys.exit(1)

    sys.exit(main(sys.argv[1:]))
