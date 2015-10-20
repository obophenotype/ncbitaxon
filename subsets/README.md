# NCBITaxon Ontology Subsets

## taxslim

Currently the main subset is taxslim. For construction details, see
the [Makefile](Makefile).

The slim is intended to cover:

 * Anything used in a taxon constraint in an ontology
 * All UniProt Reference Proteomes
 * Any taxon that has a non-IEA annotation in GO

OBO NCBITaxon administrators can add to the slim by adding to
[taxon-subset-ids.txt](taxon-subset-ids.txt). This will ensure the
taxon plus ancestors are included in the slim the next release.


