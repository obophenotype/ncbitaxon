# Requirements for this Makefile
# * owltools script is in the PATH
# * full NCBI taxononmy in OBO is in the parent folder
TODAY ?=                    $(shell date +%Y-%m-%d)
VERSION=                    $(TODAY)
ONTBASE= http://purl.obolibrary.org/obo/ncbitaxon
 
all: taxslim taxslim-disjoint-over-in-taxon.owl taxslim-disjoint-diff.md

taxslim: taxon-subset-ids.txt
	OWLTOOLS_MEMORY=8G owltools ../ncbitaxon.obo --create-slim --output-owl taxslim.owl --output-obo taxslim.obo --old-obo taxslim.obo --iri $(ONTBASE)/subsets/taxslim.owl --ids taxon-subset-ids.txt
	robot annotate -i taxslim.owl --ontology-iri $(ONTBASE)/subsets/taxslim.owl annotate -V $(ONTBASE)/releases/$(VERSION)/subsets/taxslim.owl --annotation owl:versionInfo $(VERSION) -o taxslim.owl
	robot convert -i taxslim.owl -f json -o taxslim.json

taxslim-disjoint-over-in-taxon.owl: taxslim
	owltools taxslim.owl --create-taxon-disjoint-over-in-taxon --root NCBITaxon:1
	robot query --input taxslim.owl --format ttl --query add-taxon-disjoints.ru $@.tmp.ttl
	robot merge --input $@ --input $@.tmp.ttl --collapse-import-closure false \
	      annotate -V $(ONTBASE)/releases/$(VERSION)/subsets/$@ --annotation owl:versionInfo $(VERSION) --output $@.tmp.owl && mv $@.tmp.owl $@
	rm $@.tmp.ttl

taxslim-disjoint-diff.md: taxslim-disjoint-over-in-taxon.owl
	wget http://purl.obolibrary.org/obo/ncbitaxon/subsets/$< -O current_taxslim-disjoint.owl
	robot diff --labels true --left current_taxslim-disjoint.owl --right $< -f markdown -o $@

## The following should not be run as part of CI job.
## Admin for this project should run and check in results.
##
## make new-taxon-subset-ids.txt
## cp new-taxon-subset-ids.txt taxon-subset-ids.txt
## git commit -m 'regenerated'

# reference proteome
rp-README.txt:
	wget ftp://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/reference_proteomes/README -O $@


rp-subset.obo: rp-README.txt
	./util/rpreadme2obo.pl  $< > $@

rpids.txt: rp-subset.obo

gene_association.goa_uniprot_noiea.gz:
	wget http://www.geneontology.org/gene-associations/$@ -O $@

go-tax-ids.txt: gene_association.goa_uniprot_noiea.gz
	gzip -dc $< | cut -f13 | grep ^taxon: | sort -u | perl -npe 's@^taxon:@NCBITaxon:@g;s@\|@\n@' > $@.tmp && sort -u $@.tmp > $@

new-taxon-subset-ids.txt: taxon-subset-ids.txt rpids.txt go-tax-ids.txt
	sort -u $^ > $@

