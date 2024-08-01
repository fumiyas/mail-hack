#!/usr/bin/env perl
##
## Perl-version safecat(1) clone
## Copyright (c) 2004-2007 SATOH Fumiyasu @ OSS Technology, Corp., Japan
##               <https://github.com/fumiyas/mail-filters>
##               <http://www.OSSTech.co.jp/>
##
## SPDX-License-Identifier: GPL-2.0-or-later
## Date: 2007-07-18, since 2004-06-10
##

use strict;
use warnings;
use English;
use Errno;
use IO::File;
use Sys::Hostname;
use Time::HiRes;

sub pwarn {
  print STDERR "$0: WARNING: $_[0]\n";
}

sub perr {
  print STDERR "$0: ERROR: $_[0]\n";
}

sub pdie {
  perr($_[0]);
  exit(defined($_[1]) ? $_[1] : 1);
}

if (@ARGV != 2) {
    print "Usage: $0 TEMPDIR DESTDIR\n";
    exit(1);
}

my ($tmp_dir, $dst_dir) = @ARGV;

my $pid = $PROCESS_ID;
my $hostname = Sys::Hostname::hostname();

my ($tmp_file, $dst_file);
for (my $try = 1; ; $try++) {
  my ($sec, $usec) = Time::HiRes::gettimeofday();
  my $uniqname = "${sec}.M${usec}P${pid}.${hostname}";
  $tmp_file = "$tmp_dir/$uniqname";
  $OS_ERROR = 0;
  if (!stat($tmp_file) && $OS_ERROR == Errno::ENOENT) {
    $dst_file = "$dst_dir/$uniqname";
    last;
  }

  if ($try == 10) {
    pdie "Cannot determin temporary file name: Try again";
  }

  sleep(2);
}

$SIG{'ALRM'} = sub {
  unlink($tmp_file);
  pdie "Timer has expired: Try again";
};
alarm(86400);

my $fh = IO::File->new($tmp_file, O_RDWR|O_CREAT|O_EXCL);
if (!$fh) {
  pdie "Cannot open temporary file: $OS_ERROR";
}

$OS_ERROR = 0;
while (STDIN->read(my $buf, 32768)) {
  ## FIXME: Catch and release EINTR?
  if (!$fh->write($buf)) {
    ## FIXME: Catch and release EINTR?
    my $e = "Cannot write to tempoary file: $OS_ERROR";
    unlink($tmp_file);
    pdie $e;
  }
}
if (!STDIN->eof) {
  my $e = "Cannot read from standard input: $OS_ERROR";
  unlink($tmp_file);
  pdie $e;
}
if (!$fh->sync) {
  my $e = "Cannot sync temporary file: $OS_ERROR";
  unlink($tmp_file);
  pdie $e;
}
if (!$fh->close) {
  my $e = "Cannot close temporary file: $OS_ERROR";
  unlink($tmp_file);
  pdie $e;
}

if (!link($tmp_file, $dst_file)) {
  my $e = "Cannot link temporary file to destination file: $OS_ERROR";
  unlink($tmp_file);
  pdie $e;
}

alarm(0);
if (!unlink($tmp_file)) {
  pwarn "Cannot unlink temporary file: $OS_ERROR";
}

print "$dst_file\n";

exit(0);

