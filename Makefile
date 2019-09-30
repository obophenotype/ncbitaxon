all: ncbitaxon.obo
NCBI_MEMORY=12G
OORT_MEMORY=$(NCBI_MEMORY)

test: taxonomy.dat taxdmp.zip

taxonomy.dat:
	curl ftp://ftp.ebi.ac.uk/pub/databases/taxonomy/$@ -o $@.tmp && mv $@.tmp $@

taxdmp.zip:
	curl ftp://ftp.ncbi.nih.gov/pub/taxonomy/$@ -o $@.tmp && mv $@.tmp $@

ncbitaxon.owl: taxonomy.dat taxdmp.zip
	NCBI_MEMORY=$(NCBI_MEMORY) ncbi2owl -t
.PRECIOUS: ncbitaxon.owl

ncbitaxon.obo: ncbitaxon.owl
	OWLTOOLS_MEMORY=$(NCBI_MEMORY) owltools $< -o -f obo $@.tmp && mv $@.tmp $@
##	OORT_MEMORY=$(OORT_MEMORY) ontology-release-runner --ignoreLock --skip-release-folder --skip-format owx --skip-format owl --no-subsets --outdir . --simple --allow-overwrite --no-reasoner $<

#ncbitaxon.owl: ncbitaxon-src.obo
#	ontology-release-runner --allow-overwrite --outdir . --no-reasoner --asserted $<
# requires go-perl
#ncbitaxon-src.obo: taxonomy.dat
#	go2obo -f ncbi_taxonomy $< > $@.tmp && mv $@.tmp $@
#.PRECIOUS: ncbitaxon-src.obo
