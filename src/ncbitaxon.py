#!/usr/bin/env python3

import argparse
import io
import zipfile

from collections import defaultdict
from datetime import date

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

predicates = {
    "acronym": broad_synonym,
    "anamorph": related_synonym,
    "blast name": related_synonym,
    "common name": exact_synonym,
    "equivalent name": exact_synonym,
    "genbank acronym": broad_synonym,
    "genbank anamorph": related_synonym,
    "genbank common name": exact_synonym,
    "genbank synonym": related_synonym,
    "in-part": related_synonym,
    "misnomer": related_synonym,
    "misspelling": related_synonym,
    "synonym": related_synonym,
    "scientific name": exact_synonym,
    "teleomorph": related_synonym,
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
            predicate = predicates[name_class]
            synonym_type = label_to_id(name_class)
            output.append(
                f"""
NCBITaxon:{tax_id} {predicate} "{synonym}"^^xsd:string .
[ a owl:Axiom
; owl:annotatedSource NCBITaxon:{tax_id}
; owl:annotatedProperty {predicate}
; owl:annotatedTarget "{synonym}"^^xsd:string
; oboInOwl:hasSynonymType ncbitaxon:{synonym_type}
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
            print(f"WARN Unrecognized rank '{rank}'")
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
        output.write(
            f"""@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix obo: <http://purl.obolibrary.org/obo/> .
@prefix oboInOwl: <http://www.geneontology.org/formats/oboInOwl#> .
@prefix terms: <http://purl.org/dc/terms/> .
@prefix ncbitaxon: <http://purl.obolibrary.org/obo/ncbitaxon#> .
@prefix NCBITaxon: <http://purl.obolibrary.org/obo/NCBITaxon_> .
@prefix : <http://purl.obolibrary.org/obo/ncbitaxon.owl#> .

<http://purl.obolibrary.org/obo/ncbitaxon.owl> a owl:Ontology
; owl:versionIRI <http://purl.obolibrary.org/obo/ncbitaxon/{isodate}/ncbitaxon.owl>
; rdfs:comment "Built by https://github.com/obophenotype/ncbitaxon"^^xsd:string
.

obo:IAO_0000115 a owl:AnnotationProperty
; rdfs:label "definition"^^xsd:string
.

ncbitaxon:has_rank a owl:AnnotationProperty
; obo:IAO_0000115 "A metadata relation between a class and its taxonomic rank (eg species, family)"^^xsd:string
; rdfs:label "has_rank"^^xsd:string
; rdfs:comment "This is an abstract class for use with the NCBI taxonomy to name the depth of the node within the tree. The link between the node term and the rank is only visible if you are using an obo 1.3 aware browser/editor; otherwise this can be ignored"^^xsd:string
; oboInOwl:hasOBONamespace "ncbi_taxonomy"^^xsd:string
; terms:license "NCBI organismal classification"
; terms:license "An ontology representation of the NCBI organismal taxonomy"
; terms:license <https://creativecommons.org/publicdomain/zero/1.0/>
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
        for label, parent in predicates.items():
            predicate = label_to_id(label)
            parent = parent.replace("oboInOwl", "oio")
            output.write(
                f"""
ncbitaxon:{predicate} a owl:AnnotationProperty
; rdfs:label "{label}"^^xsd:string
; oboInOwl:hasScope "{parent}"^^xsd:string
; rdfs:subPropertyOf oboInOwl:SynonymTypeProperty
.
"""
            )

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
                        synonyms[tax_id].append([name, unique, "scientific name"])

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
