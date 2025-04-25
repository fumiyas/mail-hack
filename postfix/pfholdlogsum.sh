#!/bin/sh
##
## Postfix: Summarize header_checks(5) hold logs
##
## SPDX-FileCopyrightText: 2018-2024 SATOH Fumiyasu @ OSSTech Corp., Japan
## SPDX-License-Identifier: GPL-3.0-or-later
##

if [ "${1-}" = "-h" ]; then
  echo "Usage: ${0##*/} [MAIL.LOG]"
  exit 1
fi

if [ $# -eq 0 ]; then
  set -- /var/log/mail.log
elif [ "${1-}" = "-" ]; then
  shift $#
fi

grep ' hold: header ' "$@" \
|sed -E \
  -e 's/.* hold: header //' \
  -e 's/ from [-_.A-Za-z0-9]+\[[0-9a-f.:]+\];( [a-z]+=[^ ]+)*: /\t/' \
  -e '/^From:/s/ <[^\t]+(\.[-_A-Za-z0-9]+)>/ <...@...\1>/' \
  -e '/^List-Unsubscribe:/s/<mailto:[^@>]*@[^.>]*\?[^>]*>/<mailto:...>/' \
  -e 's/(=\?[-_A-Za-z0-9]+\?[BbQq]\?[^?]+\?=)\?+/\1/g' \
  -e 's/\t/ | /' \
|(
  if type nkf >/dev/null 2>&1; then
    exec nkf -w
  else
    exec cat
  fi
) \
|sort \
|uniq -c \
|sort -nr \
;
