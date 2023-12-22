#!/bin/bash
##
## Generate a DNS TXT record for DomainKeys (DKIM) from a private key file
## Copyright (c) 2023 SATOH Fumiyasu @ OSSTech Corp., Japan
##
## License: GNU General Public License version 3
##

set -u
set -e
set -o pipefail || exit $?

if [ -t 0 ]; then
  _pdeco_reset=$(tput sgr0)
  _pdeco_info=$(tput setaf 2)
  _pdeco_warn=$(tput setaf 3)
  _pdeco_error=$(tput setaf 1)
else
  _pdeco_reset=''
  _pdeco_info=''
  _pdeco_warn=''
  _pdeco_error=''
fi

pinfo() {
  echo "$0: ${_pdeco_info}INFO${_pdeco_reset}: $1" 1>&2
}

pwarn() {
  echo "$0: ${_pdeco_warn}WARNING${_pdeco_reset}: $1" 1>&2
}

perr() {
  echo "$0: ${_pdeco_error}ERROR${_pdeco_reset}: $1" 1>&2
}

pdie() {
  perr "$1"
  exit "${2-1}"
}

## ======================================================================

openssl_command="openssl"
python_command="python3"

key_ttl=''
key_version='DKIM1'
key_flags=''
key_service='email'
key_granularity=''
key_description=''

# shellcheck disable=SC2317
getopts_want_arg()
{
  if [[ $# -lt 2 ]]; then
    pdie "Option requires an argument: $1"
  fi
  if [[ -n ${3:+set} ]]; then
    if [[ $2 =~ $3 ]]; then
      : OK
    else
      pdie "Invalid value for option: $1: $2"
    fi
  fi
  if [[ -n ${4:+set} ]]; then
    if [[ $2 =~ $4 ]]; then
      pdie "Invalid value for option: $1: $2"
    fi
  fi
}

while [[ $# -gt 0 ]]; do
  opt="$1"; shift

  if [[ -z "${opt##-[!-]?*}" ]]; then
    set -- "-${opt#??}" ${1+"$@"}
    opt="${opt%"${1#-}"}"
  fi
  if [[ -z "${opt##--*=*}" ]]; then
    set -- "${opt#--*=}" ${1+"$@"}
    opt="${opt%%=*}"
  fi

  case "$opt" in
  --ttl)
    getopts_want_arg "$opt" ${1+"$1"} ${1+"^[1-9][0-9]+$"}
    key_ttl="$1"; shift
    ;;
  --version)
    getopts_want_arg "$opt" ${1+"$1"} ${1+'^[-._0-9A-Za-z]+$'}
    key_version="$1"; shift
    ;;
  -t|--test)
    key_flags="${key_flags:+$key_flags:}y"
    ;;
  -s|--service)
    getopts_want_arg "$opt" ${1+"$1"} ${1+'^[-._0-9A-Za-z]+$'}
    key_service="$1"; shift
    ;;
  -g|--granularity)
    getopts_want_arg "$opt" ${1+"$1"} ${1+. '[;]'}
    key_granularity="$1"; shift
    ;;
  -d|--description)
    getopts_want_arg "$opt" ${1+"$1"}
    if ! key_description="$("$python_command" -m quopri -t <<<"$1" |tr -d '\n')"; then
      pdie "Failed to encode description into quoted-printable string: Command failed: $?"
    fi
    shift
    ;;
  --)
    break
    ;;
  -*)
    pdie "Invalid option: $opt"
    ;;
  *)
    set -- "$opt" ${1+"$@"}
    break
    ;;
  esac
done

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 [OPTIONS] KEY_FILE KEY_SELECTOR KEY_DOMAIN"
  exit 1
fi

key_file="$1"; shift
key_selector="$1"; shift
key_domain="$1"; shift

## ----------------------------------------------------------------------

key_type=$(
  "$openssl_command" pkey \
    -in "$key_file" \
    -text \
    -noout \
  |sed -n '1s/ .*//p' \
  |tr A-Z a-z \
  ;
)
if [[ $key_type == 'private-key:' ]]; then
  ## OpenSSL 3.0 does NOT show the key type for RSA
  key_type='rsa'
fi

## ======================================================================

printf '%s._domainkey.%s.%s IN TXT ( "%s%s%s%s%s%s p="\n' \
  "$key_selector" \
  "$key_domain" \
  "${key_ttl:+ $key_ttl}" \
  "${key_version:+ v=$key_version;}" \
  "${key_flags:+ t=$key_flags;}" \
  "${key_service:+ s=$key_service;}" \
  "${key_granularity:+ g=$key_granularity;}" \
  "${key_description:+ n=$key_description;}" \
  "${key_type:+ k=$key_type;}" \
;
"$openssl_command" pkey \
  -in "$key_file" \
  -pubout \
|sed '/^-/d' \
|tr -d '\n' \
|sed -E 's/(.{250})/\1\n/g' \
|sed 's/^/    "/; s/$/"/' \
;
echo ')'
