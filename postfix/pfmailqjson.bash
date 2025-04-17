#!/bin/bash
##
## Postfix: List the mail queue in JSON format
##
## SPDX-FileCopyrightText: 2025 SATOH Fumiyasu @ OSSTech Corp., Japan
## SPDX-License-Identifier: GPL-3.0-or-later
##

set -u
set -o pipefail || exit $?  # bash 3.0+

perr() {
  echo "$0: ERROR: $1" 1>&2
}

pdie() {
  perr "$1"
  exit "${2-1}"
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "\
Usage: ${0##*/} QUEUE_NAME [AGE]

QUEUE_NAME
  all, hold, incoming, active or deferred
AGE
  List only queues older than the number of days
"
  exit 1
fi

queue_name="${1-all}"; ${1+shift}
days_old="${1-}"; ${1+shift}

jq_options=(
  --arg queue_name "$queue_name"
)

if [[ -n $days_old ]]; then
  seconds_old="${days_old%[smhd]}"
  if [[ $seconds_old == *[!0-9]* ]]; then
    pdie "Invalid AGE format: $days_old"
  fi
  case "$days_old" in
  *s)
    ;;
  *m)
    ((seconds_old *= 60))
    ;;
  *h)
    ((seconds_old *= 60 * 60))
    ;;
  *)
    ((seconds_old *= 60 * 60 * 24))
    ;;
  esac
  jq_options+=(
    --argjson time_limit "$(($(date +%s) - seconds_old))"
  )
else
  jq_options+=(
    --argjson time_limit 0
  )
fi

# jq 1.7.1: strflocaltime always outputs +0000 for %z
# https://github.com/jqlang/jq/issues/2429

postqueue -j \
|jq \
  "${jq_options[@]}" \
  '
    select(($queue_name == "all") or (.queue_name == $queue_name))
    |select(($time_limit == 0) or (.arrival_time <= $time_limit))
    |(
      .arrival_datetime = (.arrival_time | strflocaltime("%FT%T %Z"))
      #.arrival_datetime = (.arrival_time | strflocaltime("%FT%T%z"))
    )
  ' \
;
