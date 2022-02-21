<!--[![Build Status](https://travis-ci.org/obophenotype/ncbitaxon.svg?branch=master)](https://travis-ci.org/obophenotype/ncbitaxon)-->
[![DOI](https://zenodo.org/badge/13996/obophenotype/ncbitaxon.svg)](https://zenodo.org/badge/latestdoi/13996/obophenotype/ncbitaxon)


# Build for NCBITaxon Ontology

The NCBITaxon ontology is an automatic translation of the [NCBI taxonomy database](http://www.ncbi.nlm.nih.gov/taxonomy) into obo/owl.

# Details

For details on using the ontology, see the OBO page:

http://obofoundry.org/ontology/ncbitaxon.html

This README details with technical aspects of the build

## Releases

**Outdated, see end of README for updated instructions**

Releases of the obo/owl happen when the [Continuous Integration
Job](https://ci.monarchinitiative.org/view/pipelines/job/ncbi_taxon/) is manually
triggered. Currently this must be done by an OBO administrator. There
is currently no fixed cycle, and this is generally done on demand. The
team that informally handles this are:

 * James Overton, IEBD/OBO
 * Heiko Dietze, LBNL/GO
 * Frederic Bastian, BgeeDb/Uberon
 * Chris Mungall, LBNL/GO/Monarch/Uberon/OBO
 * Peter Midford, Phenoscape
 * Bill Duncan (LBNL)
 * Nicolas Matentzoglu (EMBL-EBI)

## Subsets

Currently there is one subset, ncbitaxon/subsets/taxslim - for details, see [subsets/README.md](subsets/README.md)

## Licensing

The license for this software is BSD3. See the [LICENSE](LICENSE) file.

Note that the *content* of the ontology is not covered by this software license. The content comes from NCBI.

## Citing the NCBITaxon ontology

before citing, ask yourself what the artefact you wish to cite is:

 * The NCBI taxonomy **database**
 * The OBO/OWL rendering of the NCBI taxonomy database

The latter is a fairly trivial translation of the former. If you are in any way citing the *contents* then **you should cite the database**. Currently the most up to date reference is:

 * Federhen, Scott. **The NCBI taxonomy database.** *Nucleic acids research 40.D1 (2012): D136-D143.* [http://nar.oxfordjournals.org/content/40/D1/D136.short](http://nar.oxfordjournals.org/content/40/D1/D136.short)

If you specifically wish to cite the OBO/OWL translation, use the URL for this page

## Editors guide for running releases

### Using gh for releases

1. `sh odk.sh bash` (to enter ODK container)
   1. `make clean all -B`
   2. `cd subsets`
   3. `make all -B`
   4. `cd ..`
2. gh release create v2021-06-10
3. gh release upload v2021-06-10  ncbitaxon.json ncbitaxon.json.gz ncbitaxon.obo ncbitaxon.obo.gz ncbitaxon.owl ncbitaxon.owl.gz subsets/taxslim-disjoint-over-in-taxon.owl subsets/taxslim.obo subsets/taxslim.owl subsets/taxslim.json

### Using Monarch Jenkins

1. Trigger the Jenkins Job on [ci.monarchinitiative.org](https://ci.monarchinitiative.org/view/pipelines/job/ncbi_taxon/)
2. Download all generated files from the Jenkins job (except for env.txt), including the files in the [subset](https://ci.monarchinitiative.org/view/pipelines/job/ncbi_taxon/lastSuccessfulBuild/artifact/subsets/) directory.
3. On GitHub, go to [Code](https://github.com/obophenotype/ncbitaxon), and click on [releases](https://github.com/obophenotype/ncbitaxon/releases).
4. Click "Draft a new release". The tag is something like `v2020-02-28`. Provide a title and a meaningful description, and upload all the files downloaded from the Jenkins job above. Hit `Publish release`.

