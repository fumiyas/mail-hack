#!/bin/sh
##
## Postfix: Catch all mail messages
## Copyright (c) 2023 SATOH Fumiyasu @ OSSTech Corp., Japan
##
## /etc/postfix/main.cf:
## transport_maps=hash:$config_directory/transport
## catchall_destination_recipient_limit=1
##
## /etc/postfix/master.cf:
## catchall  unix  -       n       n       -       -       pipe
##   flags=DRXhu user=mail argv=/usr/local/libexec/postfix/catchall ${recipient}
##
## /etc/postfix/transport:
## excepted-one-domain.example.com      :
## .excepted-sub-domains.example.jp     :
## *                                    catchall
##
## install -d -m 0755 /usr/local/libexec/postfix
## install -m 0755 postfix-catchall.sh /usr/local/libexec/postfix/catchall
## postconf -e catchall_destination_recipient_limit=1
## postconf -M catchall/unix='catchall unix - n n - - pipe flags=DRXhu user=mail argv=/usr/local/libexec/postfix/catchall ${recipient}'
##

set -u
umask 0077

## ======================================================================

## sysexits.h
EX_DATAERR=65
EX_NOUSER=67
EX_NOHOST=68
EX_UNAVAILABLE=69
EX_SOFTWARE=70
EX_OSERR=71
EX_CANTCREAT=73
EX_TEMPFAIL=75
EX_NOPERM=77

## ----------------------------------------------------------------------

perr() {
  echo "$0: ERROR: $1" 1>&2
}

pdie() {
  perr "$1"
  exit "${2-1}"
}

## ======================================================================

recipient="$1"

if [ -n "${recipient##*@*}" ] || [ -z "${recipient##*/*}" ]; then
  pdie "Invalid recipient: $recipient" "$EX_DATAERR"
fi

local_name="${recipient%@*}"
local_extension="${local_name#*+}"

case "$local_extension" in
error-nouser)
  exit "$EX_NOUSER"
  ;;
error-nohost)
  exit "$EX_NOHOST"
  ;;
error-unavailable)
  exit "$EX_UNAVAILABLE"
  ;;
error-software)
  exit "$EX_SOFTWARE"
  ;;
error-tempfail)
  exit "$EX_TEMPFAIL"
  ;;
error-noperm)
  exit "$EX_NOPERM"
  ;;
esac

## ----------------------------------------------------------------------

timestamp="$(date '+%FT%T')" || pdie "Failed to generate timestamp ($?)" "$EX_OSERR"
mailbox_base="/var/mail/catchall/${timestamp%%T*}"
mailbox_dir="$mailbox_base/$recipient"

## ======================================================================

if [ ! -d "$mailbox_dir" ]; then
  mkdir -p -- "$mailbox_dir" || pdie "Failed to create mailbox directory ($?): $mailbox_dir" "$EX_CANTCREAT"
fi

if [ ! -w "$mailbox_dir" ]; then
  pdie "Mailbox directory not writeable: $mailbox_dir" "$EX_NOPERM"
fi

for n in 0 1 2 3 4 5 6 7 8 9 timeout; do
  if [ "$n" = 'timeout' ]; then
    pdie "Failed to determine out filename" "$EX_TEMPFAIL"
  fi
  mail_file="$mailbox_dir/$timestamp.$n.$$.eml"
  if ( set -C; : >"$mail_file" ); then
    break
  fi
  sleep 1
done

cat >"$mail_file" || pdie "Failed to save mail message" "$EX_CANTCREAT"
