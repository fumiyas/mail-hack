#!/usr/bin/env python3
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

DSN_TEXT_BY_STATUS = {
    "X.0.0": "Other undefined Status",
    "X.1.0": "Other address status",
    "X.1.1": "Bad destination mailbox address",
    "X.1.2": "Bad destination system address",
    "X.1.3": "Bad destination mailbox address syntax",
    "X.1.4": "Destination mailbox address ambiguous",
    "X.1.5": "Destination address valid",
    "X.1.6": "Destination mailbox has moved, No forwarding address",
    "X.1.7": "Bad sender's mailbox address syntax",
    "X.1.8": "Bad sender's system address",
    "X.1.9": "Message relayed to non-compliant mailer",
    "X.1.10": "Recipient address has null MX",
    "X.2.0": "Other or undefined mailbox status",
    "X.2.1": "Mailbox disabled, not accepting messages",
    "X.2.2": "Mailbox full",
    "X.2.3": "Message length exceeds administrative limit",
    "X.2.4": "Mailing list expansion problem",
    "X.3.0": "Other or undefined mail system status",
    "X.3.1": "Mail system full",
    "X.3.2": "System not accepting network messages",
    "X.3.3": "System not capable of selected features",
    "X.3.4": "Message too big for system",
    "X.3.5": "System incorrectly configured",
    "X.3.6": "Requested priority was changed",
    "X.4.0": "Other or undefined network or routing status",
    "X.4.1": "No answer from host",
    "X.4.2": "Bad connection",
    "X.4.3": "Directory server failure",
    "X.4.4": "Unable to route",
    "X.4.5": "Mail system congestion",
    "X.4.6": "Routing loop detected",
    "X.4.7": "Delivery time expired",
    "X.5.0": "Other or undefined protocol status",
    "X.5.1": "Invalid command",
    "X.5.2": "Syntax error",
    "X.5.3": "Too many recipients",
    "X.5.4": "Invalid command arguments",
    "X.5.5": "Wrong protocol version",
    "X.5.6": "Authentication Exchange line is too long",
    "X.6.0": "Other or undefined media error",
    "X.6.1": "Media not supported",
    "X.6.2": "Conversion required and prohibited",
    "X.6.3": "Conversion required but not supported",
    "X.6.4": "Conversion with loss performed",
    "X.6.5": "Conversion Failed",
    "X.6.6": "Message content not available",
    "X.6.7": "Non-ASCII addresses not permitted for that",
    "X.6.8": "UTF-8 string reply is required, but not permitted by",
    "X.6.9": "UTF-8 header message cannot be transferred to one or",
    "X.7.0": "Other or undefined security status",
    "X.7.1": "Delivery not authorized, message refused",
    "X.7.2": "Mailing list expansion prohibited",
    "X.7.3": "Security conversion required but not possible",
    "X.7.4": "Security features not supported",
    "X.7.5": "Cryptographic failure",
    "X.7.6": "Cryptographic algorithm not supported",
    "X.7.7": "Message integrity failure",
    "X.7.8": "Trust relationship required",
    "X.7.10": "Encryption Needed",
    "X.7.13": "User Account Disabled",
    "X.7.14": "Trust relationship required",
    "X.7.15": "Priority Level is too low",
    "X.7.16": "Message is too big for the specified priority",
    "X.7.17": "Mailbox owner has changed",
    "X.7.18": "Domain owner has changed",
    "X.7.19": "RRVS test cannot be completed",
    "X.7.20": "No passing DKIM signature found",
    "X.7.21": "No acceptable DKIM signature found",
    "X.7.22": "No valid author-matched DKIM signature found",
    "X.7.23": "SPF validation failed",
    "X.7.24": "SPF validation error",
    "X.7.25": "Reverse DNS validation failed",
    "X.7.26": "Multiple authentication checks failed",
    "X.7.27": "Sender address has null MX",
    }


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
    csv_writer.writerow(('Address', 'Date', 'Status', 'Status-Text', 'Diagnostic-Code'))

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

        dsn_status = bounced_info['dsn'].get('status')
        try:
            dsn_status_x = re.sub(r'^[0-9]+', 'X', dsn_status)
        except TypeError:
            pass
        csv_writer.writerow([
            bounced_info['address'],
            bounced_info['date'],
            dsn_status,
            DSN_TEXT_BY_STATUS.get(dsn_status_x),
            bounced_info['dsn'].get('diagnostic-code'),
            ])

    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: %s FILENAME [...]" % (sys.argv[0]), file=sys.stderr)
        sys.exit(1)

    sys.exit(main(sys.argv[1:]))
