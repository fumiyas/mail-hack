#!/bin/bash
##
## Mail to text translator
## Copyright (c) 2013 SATOH Fumiyasu @ OSS Technlogy Corp., Japan
##
## SPDX-License-Identifier: GPL-3.0-or-later
##
## Required external commands:
##   reformime(1) from maildrop
##   nkf(1)
##   pdftotext(1) from poppler
##   wvWare(1)
##   xlhtml(1)
##   ppthtml(1) from xlhtml
##   unzip(1)
##

set -u

file_name="${FILENAME-}"
file_type="${CONTENT_TYPE-}"

if [ -z "$file_name$file_type" ]; then
  exec reformime -X "$0"
  exit 1
fi

perr()
{
  echo "$0: ERROR: $1" 1>&2
}

pdie()
{
  perr "$1"
  exit "${2-1}"
}

html2text() {
  ## FIXME &#XXXX;
  sed \
    -e 's/<[^>]*>//g' \
    -e 's/&nbsp;/ /g' \
    -e 's/&quot;/"/g' \
    -e 's/&gt;/>/g' \
    -e 's/&lt;/</g' \
    -e 's/&amp;/\&/g' \
    -e '/^ *$/d' \
  ;
}

xml2text() {
  ## FIXME &#XXXX;
  sed \
    -e 's/<[^>]*>//g' \
    -e 's/&nbsp;/ /g' \
    -e 's/&quot;/"/g' \
    -e "s/&apos;/'/g" \
    -e 's/&gt;/>/g' \
    -e 's/&lt;/</g' \
    -e 's/&amp;/\&/g' \
    -e '/^ *$/d' \
  ;
}

odf2text() {
  unzip -p "$1" 'meta.xml' 'content.xml' \
  |xml2text \
  ;
}

openxml2text() {
  unzip -p "$@" \
  |sed \
    -e 's/<p:txBody>/ /g' \
    -e 's/<\/t>/ /g' \
  |xml2text \
  ;
}

typeset -l file_ext
file_ext=""

file_type1="${file_type%/*}"
file_type2="${file_type#*/}"

case "$file_type1" in
  text)
    case "$file_type2" in
      plain)
	file_ext="txt"
	;;
      html|xml)
	file_ext="html"
	;;
      *)
	file_ext="txt"
	;;
    esac
    ;;
  application)
    case "$file_type2" in
      x-zip-compressed)
	file_ext="zip"
	;;
      pdf|x-pdf)
	file_ext="pdf"
	;;
      msword|vnd.ms-word*)
	file_ext="doc"
	;;
      mspowerpoint|vnd.ms-powerpoint*)
	file_ext="ppt"
	;;
      ms-excel|x-msexcel|vnd.ms-excel*)
	file_ext="xls"
	;;
      vnd.openxmlformats-officedocument.wordprocessingml.*)
	file_ext="docx"
	;;
      vnd.openxmlformats-officedocument.spreadsheetml.*)
	file_ext="xlsx"
	;;
      vnd.openxmlformats-officedocument.presentationml.*)
	file_ext="pptx"
	;;
      vnd.oasis.opendocument.text*)
	file_ext="odt"
	;;
      vnd.oasis.opendocument.spreadsheet*)
	file_ext="ods"
	;;
      vnd.oasis.opendocument.presentation*)
	file_ext="odp"
	;;
    esac
    ;;
esac

if [ -z "$file_ext" ]; then
  file_ext="${file_name##*.}"
fi

trap 'rm -f ${file_tmp+"$file_tmp"}' EXIT INT

case "$file_ext" in
  txt)
    cat |nkf -w
    ;;
  html)
    html2text |nkf -w
    ;;
  zip)
    unzip -l /dev/stdin |sed '1,3d;/^-/d;$d'
    ;;
  o[dt][tspg])
    odf2text /dev/stdin
    ;;
  pdf)
    file_tmp=`mktemp` || exit 1
    cat >"$file_tmp"
    pdftotext -enc UTF-8 -nopgbrk "$file_tmp" -
    ;;
  doc)
    #catdoc -d utf-8 -w /dev/stdin
    wvWare --charset=UTF-8 --nographics /dev/stdin \
    |html2text \
    ;
    ;;
  xls)
    #xls2csv -q0 /dev/stdin
    xlhtml -a -te -nc -fw /dev/stdin \
    |sed \
      -e 's/<TD[^>]*>&nbsp;//g' \
      -e 's/<TD[^>]*>/ /g' \
      -e "s/^<meta .*<\/TITLE>//" \
      -e "s/<I>Spreadsheet's Author:.*xlhtml [^<]*//" \
    |html2text \
    ;
    ;;
  ppt)
    ppthtml /dev/stdin \
    |sed \
      -e 's/^<HTML>.*//' \
      -e 's/^<hr>.*>pptHtml<.*//' \
    |html2text \
    ;
    ;;
  do[ct][xm])
    openxml2text /dev/stdin 'word/document.xml'
    ;;
  xl[st][xm])
    openxml2text /dev/stdin 'xl/sharedStrings.xml'
    ;;
  pp[ts][xm]|pot[xm]|sld[xm])
    openxml2text /dev/stdin 'ppt/slides/slide*.xml'
    ;;
  *)
    pdie "Unknown file type: $file_type ($file_name)"
    ;;
esac

