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

Note that the taxslim.obo used in this repository is *not* the release
version. The release is produced by Jenkins and consumed by the OBO
library build.

Note that if you add new IDs to `taxon-subset-ids.txt`, make sure this
is placed in alphanumeric order. If in doubt, normalize ordering use
the unix `sort` command

## disjointness GCIs

this makefile also includes a target for `taxslim-disjoint-over-in-taxon.owl`

This is GCIs of the form

    (in_taxon some A) DisjointWith (in_taxon some B)
    (in_taxon some X) DisjointWith (in_taxon some (not X)) for every taxon X

These are necessary for reasoning within the profile supported by Elk, which [does not include ONLY or Functional](https://github.com/liveontologies/elk-reasoner/wiki/OwlFeatures)

