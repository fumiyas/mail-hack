#!/usr/bin/make -f
##
## Postfix: Makefile for updating *.db files
##
## Copyright (c) 2014-2022 SATOH Fumiyasu @ OSSTech Corp., Japan
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
	@cd $(POSTFIX_CONFIG_DIR) && $(MAKE) db

.PHONY: db
db: Makefile.postmap
	@echo 'Updating $(POSTFIX_CONFIG_DIR)/*.db files ...'
	@$(MAKE) -f $(POSTFIX_CONFIG_DIR)/Makefile.postmap

Makefile.postmap: Makefile main.cf
	@echo 'Updating $@ ...'
	@set -e; \
	tmp="$@.$$$$.tmp"; \
	trap 'rm -f "$$tmp"' EXIT; \
	rm -f "$$tmp"; \
	echo 'POSTMAP=$(POSTMAP)' >>"$$tmp"; \
	echo '.PHONY: db' >>"$$tmp"; \
	echo 'db::' >>"$$tmp"; \
	{ $(POSTCONF) -c $(POSTFIX_CONFIG_DIR) || kill $$$$; } \
	|sed -n \
	  -e '/^alias_database = /d' \
	  -e '/^alias_maps = /d' \
	  -e 's/^[^=]*= *//' \
	  -e 's/, */ /g' \
	  -e '/hash:/p' \
	|tr ' ' '\n' \
	|sed -n \
	  -e 's#^hash:\$$config_directory/#$(POSTFIX_CONFIG_DIR)/#p' \
	  -e 's#^hash:$(POSTFIX_CONFIG_DIR)/#$(POSTFIX_CONFIG_DIR)/#p' \
	|sort -u \
	|while read mapfile; do \
	  echo "db:: $$mapfile.db"; \
	  echo "$$mapfile.db: $$mapfile"; \
	  echo "	\$$(POSTMAP) $$mapfile"; \
	done \
	>>"$$tmp"; \
	mv "$$tmp" $@
