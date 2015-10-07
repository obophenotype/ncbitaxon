# Requirements for this Makefile
# * owltools script is in the PATH
# * full NCBI taxononmy in OBO is in the parent folder
 
all: taxslim taxslim-disjoint-over-in-taxon.owl 

taxslim: taxon-subset-ids.txt
	OWLTOOLS_MEMORY=8G owltools ../ncbitaxon.obo --create-slim --output-owl taxslim.owl --output-obo taxslim.obo --old-obo taxslim.obo --iri http://purl.obolibrary.org/obo/ncbitaxon/subsets/taxslim.owl --ids taxon-subset-ids.txt

taxslim-disjoint-over-in-taxon.owl: taxslim
	owltools taxslim.owl --create-taxon-disjoint-over-in-taxon --root NCBITaxon:1

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

new-taxon-subset-ids.txt: taxon-subset-ids.txt rpids.txt
	sort -u $^ > $@
