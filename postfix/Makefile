#!/usr/bin/make -f
##
## Postfix: Makefile for updating database files
##
## SPDX-FileCopyrightText: 2014-2025 SATOH Fumiyasu @ OSSTech Corp., Japan
## SPDX-License-Identifier: WTFPL
##
## <https://github.com/fumiyas/mail-filters/blob/master/postfix/Makefile>
## <https://fumiyas.github.io/>
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
	  { \
	    $(POSTCONF) -x -c $(POSTFIX_CONFIG_DIR) || kill $$$$; \
	    $(POSTCONF) -M -x -c $(POSTFIX_CONFIG_DIR) || kill $$$$; \
	  } \
	  |sed -E \
	    -e '/^alias_(database|maps) = /d' \
	  |grep -E -o ' (lmdb|cdb|hash):$(POSTFIX_CONFIG_DIR)/[^, ]+' \
	  |sort -u \
	  |while IFS=' :' read -r type src; do \
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
