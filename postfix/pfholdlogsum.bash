#!/bin/bash
##
## Postfix: Summarize header_checks(5) hold logs
##
## SPDX-FileCopyrightText: 2018-2024 SATOH Fumiyasu @ OSSTech Corp., Japan
## SPDX-License-Identifier: GPL-3.0-or-later
##

export LC_CTYPE=C.UTF-8

## U+00A0 NO-BREAK SPACE
## U+200B ZERO WIDTH SPACE
## U+200C ZERO WIDTH NON-JOINER
## U+200D ZERO WIDTH JOINER
## U+FEFF ZERO WIDTH NO-BREAK SPACE
u_space=$(printf '\u00A0\u200B\u200C\u200D\uFEFF')
## U+0332 COMBINING LOW LINE
## U+034E COMBINING UPWARDS ARROW BELOW
u_combining=$(printf '\u0332\u034E')

if [ "${1-}" = "-h" ]; then
  echo "Usage: ${0##*/} [MAIL.LOG]"
  exit 1
fi

if [ $# -eq 0 ]; then
  set -- /var/log/mail.log
elif [ "${1-}" = "-" ]; then
  shift $#
fi

sed -E -n '
  s/^[^ ]+ [^ ]+ [^ ]+ [^ ]+ (hold|reject|discard): header (.*) from [-_.A-Za-z0-9]+\[[0-9a-f.:]+\];( [a-z]+=[^ ]+)*: /\1: \2\t/
  ## Next if no s/// has done
  T
  ## Mask local and domain part in e-mail addresses
  /^[a-z]+: From:/s/ <[^\t]+(\.[-_A-Za-z0-9]+)>/ <...@...\1>/
  ## Mask e-mail address in URLs
  /^[a-z]+: List-Unsubscribe:/s/<mailto:[^@>]*@[^.>]*\?[^>]*>/<mailto:...>/
  ## Remove masked LF and tab in syslog log
  s/(=\?[-_A-Za-z0-9]+\?[BbQq]\?[^?]+\?=)\?+/\1/g
  ## Add a separator
  s/\t/ | /
  p
  ' \
  -- \
  "$@" \
|(
  if type nkf >/dev/null 2>&1; then
    exec nkf -w
  else
    exec cat
  fi
) \
|sed -E \
  -e "s/([$u_space$u_combining])/[\1]/g" \
|sort \
|uniq -c \
|sort -nr \
;
