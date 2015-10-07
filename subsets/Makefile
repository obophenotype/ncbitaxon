# Requirements for this Makefile
# * owltools script is in the PATH
# * full NCBI taxononmy in OBO is in the parent folder
 
all: taxslim taxslim-disjoint-over-in-taxon.owl 

taxslim: taxon-subset-ids.txt
	OWLTOOLS_MEMORY=8G owltools ../ncbitaxon.obo --create-slim --output-owl taxslim.owl --output-obo taxslim.obo --old-obo taxslim.obo --iri http://purl.obolibrary.org/obo/ncbitaxon/subsets/taxslim.owl --ids taxon-subset-ids.txt

taxslim-disjoint-over-in-taxon.owl: taxslim
	owltools taxslim.owl --create-taxon-disjoint-over-in-taxon --root NCBITaxon:1
