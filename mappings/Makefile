env_eol_mapping_to_taxonomies.tar.gz:
	wget http://environments.jensenlab.org/$@ -O $@

mappings_eolids_ncbitaxids.tsv: env_eol_mapping_to_taxonomies.tar.gz
	tar -zxvf $< && touch $@

ncbitaxon-to-eol.obo: mappings_eolids_ncbitaxids.tsv
	./eolmap2obo.pl $< > $@
