#!/usr/bin/make -f
##
## Postfix: Makefile for updating database files
##
## Copyright (c) 2014-2023 SATOH Fumiyasu @ OSSTech Corp., Japan
##               <https://github.com/fumiyas/mail-filters/blob/master/postfix/Makefile>
##               <https://fumiyas.github.io/>
##
## License: Do What The Fuck You Want To Public License (WTFPL) version 2
##

POSTFIX_CONFIG_DIR=	/etc/postfix
POSTCONF=		/usr/sbin/postconf
POSTMAP=		/usr/sbin/postmap

.PHONY: default
default:
	@ cd $(POSTFIX_CONFIG_DIR) && $(MAKE) database

.PHONY: database
database: Makefile.database
	@ echo 'Updating Postfix database files ...'
	@ $(MAKE) -f $(POSTFIX_CONFIG_DIR)/Makefile.database

Makefile.database: Makefile main.cf
	@ echo 'Generating $@ ...'
	@ set -e; \
	  tmp="$@.$$$$.tmp"; \
	  trap 'rm -f "$$tmp"' EXIT; \
	  rm -f "$$tmp"; \
	  echo 'POSTMAP=$(POSTMAP)' >>"$$tmp"; \
	  echo '.PHONY: database' >>"$$tmp"; \
	  echo 'database::' >>"$$tmp"; \
	  { $(POSTCONF) -c $(POSTFIX_CONFIG_DIR) || kill $$$$; } \
	  |sed -E -n \
	    -e '/^alias_(database|maps) = /d' \
	    -e 's/^[^=]+= *//' \
	    -e 's/, */ /g' \
	    -e '/(lmdb|hash):/p' \
	  |tr ' ' '\n' \
	  |sed -E -n \
	    -e 's#^(lmdb|hash):(\$$config_directory|$(POSTFIX_CONFIG_DIR))/#\1 $(POSTFIX_CONFIG_DIR)/#p' \
	  |sort -u \
	  |while read type src; do \
	    if [ "$$type" = "hash" ]; then \
	      dst="$$src.db"; \
	    else \
	      dst="$$src.$$type"; \
	    fi; \
	    echo "database:: $$dst"; \
	    echo "$$dst: $$src"; \
	    echo "	\$$(POSTMAP) $$type:$$src"; \
	  done \
	  >>"$$tmp"; \
	  mv "$$tmp" $@
