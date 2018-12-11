#!/bin/sh

echo 'DSN_TEXT_BY_STATUS = {'

{
  sed \
    -n \
    -e '1,/^Appendix A /s/^ *X\.\([0-9]\{1,\}\.[0-9]\{1,\}\)  *\(.*\)$/\1 \2/p' \
    rfc3463.txt \
  ;

  ## FIXME: Status Code in RFC 4865 is for SMTP Submission Service Extension only?
  sed \
    -n \
    -e 's/^ *X\.\([0-9]\{1,\}\.[0-9]\{1,\}\) \{1,\}\([A-Z].*\)[."]*$/\1 \2/p' \
    rfc3886.txt \
    rfc4468.txt \
    rfc4954.txt \
  ;

  ## FIXME: Missing Code (SMTP Status Code): X.7.9 (534)
  ## FIXME: Missing Code (SMTP Status Code): X.7.11 (524, 538)
  ## FIXME: Missing Code (SMTP Status Code): X.7.12 (422, 432)
  ## NOTE: X.0.0 is redescribed by RFC 5248
  ## NOTE: X.6.[6-9] in RFC 5336 were updated by RFC 6531
  ## NOTE: X.6.10 in RFC 5336 was deprecated by RFC 6531
  sed \
    -n \
    -e 's/^ *\([0-9])\)* *Code: *X\.\([0-9]\{1,\}\.[0-9]\{1,\}\)$/\2/p' \
    -e 's/^ *Sample Text: *\(.*\)$/\1/p' \
    rfc5248.txt \
    rfc6531.txt \
    rfc6710.txt \
    rfc7293.txt \
    rfc7372.txt \
    rfc7505.txt \
  |sed \
    -e '/^6\.10$/d' \
    -e 'N;s/\n/ /g'\
  |sed \
    -e '/^0\.0 /d' \
  ;
} \
|sort --version-sort \
|sed \
  -e 's/[."]$//' \
  -e 's/ /": "/' \
  -e 's/$/",/' \
  -e 's/^/    "X./' \
;

echo '    }'
