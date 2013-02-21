#!/bin/ksh
##
## OpenLDAP: Append `git log -p COMMIT~..COMMIT` to an OpenLDAP commit message
## Copyright (c) 2012-2013 SATOH Fumiyasu @ OSS Technology Corp., Japan
##
## License: GNU General Public License version 3 or later
##

## Installation instructions for Courier maildrop(1):
##
## (1) Subscribe to the openldap-commit mailing list
##
##     http://www.openldap.org/lists/mm/listinfo/openldap-commit
##
## (2) Checkout OpenLDAP git repository into your $HOME/git/openldap
##
##     $ cd
##     $ mkdir git
##     $ cd git
##     $ git clone git://git.OpenLDAP.org/openldap.git
##
## (3) Put this script into your $HOME/bin/openldap-commitmail-adjust
##
## (4) Put the following lines into your maildrop(1) maildropfilter(7):
##
## if (/^From: openldap-commit2devel@OpenLDAP.org/ && /^Subject: openldap\.git /)
## {
##    flock "$HOME/git/openldap/.git/config" {
##      xfilter "cd $HOME/git/openldap && git pull --quiet >/dev/null && $HOME/bin/openldap-commitmail-adjust"
##    }
##    to "$DEFAULT"
## }

## For zsh
builtin emulate -R ksh 2>/dev/null

set -u

boundary="--------------boundary_$$_$RANDOM"

typeset -A commits

while IFS= read -r line; do
  if [[ $line = @(Content-Type:*) ]]; then
    continue
  fi
  if [[ -z $line ]]; then
    break
  fi

  echo "$line"
done

echo "Content-Type: multipart/mixed; boundary=\"$boundary\""
echo "MIME-Version: 1.0"
echo
echo "This is a multi-part message in MIME format."

echo "--$boundary"
echo "Content-Type: text/plain; charset=UTF-8"
echo "Content-Transfer-Encoding: 8bit"
echo

while IFS= read -r line; do
  #if [[ $line = @(- Log -*) ]]; then
  #  echo "$line"
  #  break
  #fi

  echo "$line" |read -r via commit garbage
  if [[ $via = "via" ]]; then
    commits[${#commits[@]}]="$commit"
  fi

  echo "$line"
done

if [[ ${#commits[@]} -eq 0 ]]; then
  cat
  exit 0
fi

cat >/dev/null
for commit in "${commits[@]}"; do
  echo "--$boundary"
  echo "Content-Type: text/plain; charset=UTF-8"
  echo "Content-Transfer-Encoding: 8bit"
  echo
  git --no-pager log -p "$commit~..$commit" 2>&1 || exit 75
  echo
done

echo "--$boundary--"

exit 0

