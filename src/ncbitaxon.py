#!/usr/bin/env python3

import argparse
import io
import zipfile
from collections import Counter, defaultdict
from datetime import date
from textwrap import dedent

oboInOwl = {
    "SynonymTypeProperty": "synonym_type_property",
    "hasAlternativeId": "has_alternative_id",
    "hasBroadSynonym": "has_broad_synonym",
    "hasDbXref": "database_cross_reference",
    "hasExactSynonym": "has_exact_synonym",
    "hasOBOFormatVersion": "has_obo_format_version",
    "hasOBONamespace": "has_obo_namespace",
    "hasRelatedSynonym": "has_related_synonym",
    "hasScope": "has_scope",
    "hasSynonymType": "has_synonym_type",
}

exact_synonym = "oboInOwl:hasExactSynonym"
related_synonym = "oboInOwl:hasRelatedSynonym"
broad_synonym = "oboInOwl:hasBroadSynonym"

# See OMO properties at
# https://github.com/information-artifact-ontology/ontology-metadata/blob/master/src/templates/annotation_properties.tsv
predicates = {
    "acronym": (broad_synonym, "OMO:0003012", "acronym"),
    "anamorph": (related_synonym, None, None),
    "blast name": (related_synonym, None, None),
    "common name": (exact_synonym, "OMO:0003003", "layperson synonym"),
    "equivalent name": (exact_synonym, None, None),
    "genbank acronym": (broad_synonym, None, None),
    "genbank anamorph": (related_synonym, None, None),
    "genbank common name": (exact_synonym, None, None),
    "genbank synonym": (related_synonym, None, None),
    "in-part": (related_synonym, None, None),
    "misnomer": (related_synonym, "OMO:0003007", "misnomer"),
    "misspelling": (related_synonym, "OMO:0003006", "misspelling"),
    "synonym": (related_synonym, None, None),
    "scientific name": (exact_synonym, None, None),
    "teleomorph": (related_synonym, None, None),
}


ranks = [
    "class",
    "cohort",
    "family",
    "forma",
    "genus",
    "infraclass",
    "infraorder",
    "kingdom",
    "order",
    "parvorder",
    "phylum",
    "section",
    "series",
    "species group",
    "species subgroup",
    "species",
    "subclass",
    "subcohort",
    "subfamily",
    "subgenus",
    "subkingdom",
    "suborder",
    "subphylum",
    "subsection",
    "subspecies",
    "subtribe",
    "superclass",
    "superfamily",
    "superkingdom",
    "superorder",
    "superphylum",
    "tribe",
    "varietas",
    "strain",
    "serogroup",
    "biotype",
    "clade",
    "forma specialis",
    "isolate",
    "serotype",
    "genotype",
    "morph",
    "pathogroup",
]

nodes_fields = [
    "tax_id",  # node id in GenBank taxonomy database
    "parent_tax_id",  # parent node id in GenBank taxonomy database
    "rank",  # rank of this node (superkingdom, kingdom, ...)
    "embl_code",  # locus-name prefix; not unique
    "division_id",  # see division.dmp file
    "inherited_div_flag",  # (1 or 0) 1 if node inherits division from parent
    "genetic_code_id",  # see gencode.dmp file
    "inherited_GC_flag",  # (1 or 0) 1 if node inherits genetic code from parent
    "mitochondrial_genetic_code_id",  # see gencode.dmp file
    "inherited_MGC_flag",  # (1 or 0) 1 if node inherits mitochondrial gencode from parent
    "GenBank_hidden_flag",  # (1 or 0) 1 if name is suppressed in GenBank entry lineage
    "hidden_subtree_root_flag",  # (1 or 0) 1 if this subtree has no sequence data yet
    "comments",  # free-text comments and citations
]

UNRECOGNIZED_RANKS = Counter()


def escape_literal(text):
    return text.replace('"', '\\"')


def label_to_id(text):
    return text.replace(" ", "_").replace("-", "_")


def convert_synonyms(tax_id, synonyms):
    """Given a tax_id and list of synonyms,
    return a Turtle string asserting triples and OWL annotations on them."""
    output = []
    for synonym, unique, name_class in synonyms:
        if name_class in predicates:
            synonym = escape_literal(synonym)
            predicate, synonym_type_curie, _ = predicates[name_class]
            if synonym_type_curie is None:
                synonym_type_curie = "ncbitaxon:" + label_to_id(name_class)
            output.append(
                f"""
NCBITaxon:{tax_id} {predicate} "{synonym}"^^xsd:string .
[ a owl:Axiom
; owl:annotatedSource NCBITaxon:{tax_id}
; owl:annotatedProperty {predicate}
; owl:annotatedTarget "{synonym}"^^xsd:string
; oboInOwl:hasSynonymType {synonym_type_curie}
] ."""
            )
    return output


def convert_node(node, label, merged, synonyms, citations):
    """Given a node dictionary, a label string, and lists for merged, synonyms, and citations,
    return a Turtle string representing this tax_id."""
    tax_id = node["tax_id"]
    output = [f"NCBITaxon:{tax_id} a owl:Class"]

    label = escape_literal(label)
    output.append(f'; rdfs:label "{label}"^^xsd:string')

    parent_tax_id = node["parent_tax_id"]
    if parent_tax_id and parent_tax_id != "" and parent_tax_id != tax_id:
        output.append(f"; rdfs:subClassOf NCBITaxon:{parent_tax_id}")

    rank = node["rank"]
    if rank and rank != "" and rank != "no rank":
        if rank not in ranks:
            if rank not in UNRECOGNIZED_RANKS:
                print(f"unrecognized rank: '{rank}'")
            UNRECOGNIZED_RANKS[rank] += 1
        rank = label_to_id(rank)
        # WARN: This is a special case for backward compatibility
        if rank in ["species_group", "species_subgroup"]:
            output.append(
                f"; ncbitaxon:has_rank <http://purl.obolibrary.org/obo/NCBITaxon#_{rank}>"
            )
        else:
            output.append(f"; ncbitaxon:has_rank NCBITaxon:{rank}")

    gc_id = node["genetic_code_id"]
    if gc_id:
        output.append(f'; oboInOwl:hasDbXref "GC_ID:{gc_id}"^^xsd:string')

    for merge in merged:
        output.append(f'; oboInOwl:hasAlternativeId "NCBITaxon:{merge}"^^xsd:string')

    for pubmed_id in citations:
        output.append(f'; oboInOwl:hasDbXref "PMID:{pubmed_id}"^^xsd:string')

    output.append('; oboInOwl:hasOBONamespace "ncbi_taxonomy"^^xsd:string')
    output.append(".")

    output += convert_synonyms(tax_id, synonyms)

    return "\n".join(output)


def split_line(line):
    """Split a line from a .dmp file"""
    return [x.strip() for x in line.split("	|")]


def convert(taxdmp_path, output_path, taxa=None):
    """Given the paths to the taxdmp.zip file and an output Turtle file,
    and an optional set of tax_id strings to extract,
    read from the taxdmp.zip file, collect annotations,
    convert nodes to Turtle strings,
    and write to the output file."""
    scientific_names = defaultdict(list)
    labels = {}
    synonyms = defaultdict(list)
    merged = defaultdict(list)
    citations = defaultdict(list)
    with open(output_path, "w") as output:
        isodate = date.today().isoformat()
        ncbi_date = date.today().replace(day=1)
        output.write(
            f"""@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix obo: <http://purl.obolibrary.org/obo/> .
@prefix oboInOwl: <http://www.geneontology.org/formats/oboInOwl#> .
@prefix OMO: <http://purl.obolibrary.org/obo/OMO_> .
@prefix terms: <http://purl.org/dc/terms/> .
@prefix ncbitaxon: <http://purl.obolibrary.org/obo/ncbitaxon#> .
@prefix NCBITaxon: <http://purl.obolibrary.org/obo/NCBITaxon_> .
@prefix : <http://purl.obolibrary.org/obo/ncbitaxon.owl#> .

<http://purl.obolibrary.org/obo/ncbitaxon.owl> a owl:Ontology
; owl:versionIRI <http://purl.obolibrary.org/obo/ncbitaxon/{isodate}/ncbitaxon.owl>
; owl:versionInfo "{isodate}"^^xsd:string
; terms:title "NCBI organismal classification"
; terms:description "An ontology representation of the NCBI organismal taxonomy"
; terms:license <https://creativecommons.org/publicdomain/zero/1.0/>
; rdfs:comment "Built by https://github.com/obophenotype/ncbitaxon"^^xsd:string
; rdfs:comment "NCBI organismal taxonomy version {ncbi_date}"^^xsd:string
.

obo:IAO_0000115 a owl:AnnotationProperty
; rdfs:label "definition"^^xsd:string
.

ncbitaxon:has_rank a owl:AnnotationProperty
; obo:IAO_0000115 "A metadata relation between a class and its taxonomic rank (eg species, family)"^^xsd:string
; rdfs:label "has_rank"^^xsd:string
; rdfs:comment "This is an abstract class for use with the NCBI taxonomy to name the depth of the node within the tree. The link between the node term and the rank is only visible if you are using an obo 1.3 aware browser/editor; otherwise this can be ignored"^^xsd:string
; oboInOwl:hasOBONamespace "ncbi_taxonomy"^^xsd:string
.
"""
        )
        for predicate, label in oboInOwl.items():
            output.write(
                f"""
oboInOwl:{predicate} a owl:AnnotationProperty
; rdfs:label "{label}"^^xsd:string
.
"""
            )

        for ad_hoc_label, (parent, curie, label) in predicates.items():
            parent = parent.replace("oboInOwl", "oio")
            if curie is None and label is None:
                output.write(dedent(f"""
                    ncbitaxon:{label_to_id(ad_hoc_label)} a owl:AnnotationProperty ;
                        rdfs:label "{ad_hoc_label}"^^xsd:string ;
                        oboInOwl:hasScope "{parent}"^^xsd:string ;
                        rdfs:subPropertyOf oboInOwl:SynonymTypeProperty .
                """))
            else:
                output.write(dedent(f"""
                    {curie} a owl:AnnotationProperty ;
                        rdfs:label "{label}"^^xsd:string ;
                        rdfs:subPropertyOf oboInOwl:SynonymTypeProperty .
                """))

        with zipfile.ZipFile(taxdmp_path) as taxdmp:
            with taxdmp.open("names.dmp") as dmp:
                for line in io.TextIOWrapper(dmp):
                    tax_id, name, unique, name_class, _ = split_line(line)
                    if name_class == "scientific name":
                        labels[tax_id] = name
                        scientific_names[name].append([tax_id, unique])
                    else:
                        synonyms[tax_id].append([name, unique, name_class])

            # use unique name only if there's a conflict
            for name, values in scientific_names.items():
                tax_ids = [x[0] for x in values]
                if len(tax_ids) > 1:
                    uniques = [x[1] for x in values]
                    if len(tax_ids) != len(set(uniques)):
                        print("WARN: Duplicate unique names", tax_ids, uniques)
                    for tax_id, unique in values:
                        labels[tax_id] = unique
                        # Reason for the line below 
                        # issue #56: https://github.com/obophenotype/ncbitaxon/issues/56
                        if name != 'environmental samples':
                            synonyms[tax_id].append(
                                [name, unique, "scientific name"]
                            )

            with taxdmp.open("merged.dmp") as dmp:
                for line in io.TextIOWrapper(dmp):
                    old_tax_id, new_tax_id, _ = split_line(line)
                    merged[new_tax_id].append(old_tax_id)

            with taxdmp.open("citations.dmp") as dmp:
                for line in io.TextIOWrapper(dmp):
                    (
                        cit_id,
                        cit_key,
                        pubmed_id,
                        medline_id,
                        url,
                        text,
                        tax_id_list,
                        _,
                    ) = split_line(line)
                    # WARN: the pubmed_id is always "0", we treat medline_id as pubmed_id
                    if medline_id == "0":
                        continue
                    for tax_id in tax_id_list.split():
                        if taxa and tax_id not in taxa:
                            continue
                        citations[tax_id].append(medline_id)

            with taxdmp.open("nodes.dmp") as dmp:
                for line in io.TextIOWrapper(dmp):
                    node = {}
                    fields = split_line(line)
                    for i in range(0, min(len(fields), len(nodes_fields))):
                        node[nodes_fields[i]] = fields[i]
                    tax_id = node["tax_id"]
                    if taxa and tax_id not in taxa:
                        continue
                    result = convert_node(
                        node,
                        labels[tax_id],
                        merged[tax_id],
                        synonyms[tax_id],
                        citations[tax_id],
                    )
                    output.write(result)

            print("Summary of unrecognized ranks:")
            print(UNRECOGNIZED_RANKS)
            # TODO: delnodes

        output.write(
            """
<http://purl.obolibrary.org/obo/NCBITaxon#_taxonomic_rank> a owl:Class
; rdfs:label "taxonomic rank"^^xsd:string
; rdfs:comment "This is an abstract class for use with the NCBI taxonomy to name the depth of the node within the tree. The link between the node term and the rank is only visible if you are using an obo 1.3 aware browser/editor; otherwise this can be ignored."^^xsd:string
; oboInOwl:hasOBONamespace "ncbi_taxonomy"^^xsd:string
.
"""
        )
        for label in ranks:
            rank = label_to_id(label)
            if rank in ["species_group", "species_subgroup"]:
                iri = f"<http://purl.obolibrary.org/obo/NCBITaxon#_{rank}>"
            else:
                iri = f"NCBITaxon:{rank}"
            output.write(
                f"""
{iri} a owl:Class
; rdfs:label "{label}"^^xsd:string
; rdfs:subClassOf <http://purl.obolibrary.org/obo/NCBITaxon#_taxonomic_rank>
; oboInOwl:hasOBONamespace "ncbi_taxonomy"^^xsd:string
.
"""
            )


def main():
    parser = argparse.ArgumentParser(
        description="Convert NCBI Taxonomy taxdmp.zip to Turtle format"
    )
    parser.add_argument("taxdmp", type=str, help="The taxdmp.zip file to read")
    parser.add_argument("taxa", type=str, nargs="?", help="A list of taxa to build")
    # TODO: upper, lower
    parser.add_argument("turtle", type=str, help="The output Turtle file to write")
    args = parser.parse_args()

    taxa = None
    if args.taxa:
        taxa = set()
        with open(args.taxa) as taxalist:
            for line in taxalist:
                taxa.add(line.split()[0])

    convert(args.taxdmp, args.turtle, taxa)


if __name__ == "__main__":
    main()
