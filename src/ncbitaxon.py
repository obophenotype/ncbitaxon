#!/usr/bin/env python3

import argparse
import io
import zipfile

from collections import defaultdict
from datetime import date


exact_synonym   = 'oboInOwl:hasExactSynonym'
related_synonym = 'oboInOwl:hasRelatedSynonym'
broad_synonym   = 'oboInOwl:hasBroadSynonym'

predicates = {
  'acronym'             : broad_synonym,
  'anamorph'            : related_synonym,
  'blast name'          : related_synonym,
  'common name'         : exact_synonym,
  'equivalent name'     : exact_synonym,
  'genbank acronym'     : broad_synonym,
  'genbank anamorph'    : related_synonym,
  'genbank common name' : exact_synonym,
  'genbank synonym'     : related_synonym,
  'in-part'             : related_synonym,
  'misnomer'            : related_synonym,
  'misspelling'         : related_synonym,
  'synonym'             : related_synonym,
  'scientific name'     : exact_synonym,
  'teleomorph'          : related_synonym
}

nodes_fields = [
        "tax_id",                           # node id in GenBank taxonomy database
        "parent_tax_id",                    # parent node id in GenBank taxonomy database
        "rank",                             # rank of this node (superkingdom, kingdom, ...) 
        "embl_code",                        # locus-name prefix; not unique
        "division_id",                      # see division.dmp file
        "inherited_div_flag",               # (1 or 0) 1 if node inherits division from parent
        "genetic_code_id",                  # see gencode.dmp file
        "inherited_GC_flag",                # (1 or 0) 1 if node inherits genetic code from parent
        "mitochondrial_genetic_code_id",    # see gencode.dmp file
        "inherited_MGC_flag",               # (1 or 0) 1 if node inherits mitochondrial gencode from parent
        "GenBank_hidden_flag",              # (1 or 0) 1 if name is suppressed in GenBank entry lineage
        "hidden_subtree_root_flag",         # (1 or 0) 1 if this subtree has no sequence data yet
        "comments"                          # free-text comments and citations
]

def convert_synonyms(tax_id, synonyms):
    output = []
    for synonym, unique, name_class in synonyms:
        if name_class in predicates:
            synonym = synonym.replace('"', '\\"')
            predicate = predicates[name_class]
            synonym_type = name_class.replace(" ", "_").replace("-", "_")
            output.append(f"""
NCBITaxon:{tax_id} {predicate} "{synonym}"^^xsd:string .
[ a owl:Axiom
; owl:annotatedSource NCBITaxon:{tax_id}
; owl:annotatedProperty {predicate}
; owl:annotatedTarget "{synonym}"^^xsd:string
; oboInOwl:hasSynonymType ncbitaxon:{synonym_type}
] .""")
    return output


def convert_node(node, label, merged, synonyms, citations):
    tax_id = node["tax_id"]
    output = [f"NCBITaxon:{tax_id} a owl:Class"]

    label = label.replace('"', '\\"')
    output.append(f'; rdfs:label "{label}"^^xsd:string')

    parent_tax_id = node["parent_tax_id"]
    if parent_tax_id and parent_tax_id != "" and parent_tax_id != tax_id:
        output.append(f"; rdfs:subClassOf NCBITaxon:{parent_tax_id}")

    # TODO: cohort, subcohort
    rank = node["rank"]
    if rank and rank != "" and rank != "no rank":
        rank = rank.replace(" ", "_")
        # WARN: This is a special case for backward compatibility
        if rank in ["species_group", "species_subgroup"]:
            output.append(f"; ncbitaxon:has_rank obo:NCBITaxon#_{rank}")
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
    return [x.strip() for x in line.split("	|")]


def main():
    parser = argparse.ArgumentParser(
            description="Convert NCBI Taxonomy taxdmp.zip to Turtle format")
    parser.add_argument("prologue",
            type=str,
            help="The prologue of the Turtle file")
    parser.add_argument("taxdmp",
            type=str,
            help="The taxdmp.zip file to read")
    parser.add_argument("taxa",
            type=str,
            nargs="?",
            help="A list of taxa to build")
    parser.add_argument("turtle",
            type=str,
            help="The output Turtle file to write")
    args = parser.parse_args()

    limit = None
    #limit = 1e7 # highest tax_id is currently 2,725,057

    taxa = None
    if args.taxa:
        taxa = set()
        with open(args.taxa) as taxalist:
            for line in taxalist:
                taxa.add(line.split()[0])

    scientific_names = defaultdict(list)
    labels = {}
    synonyms = defaultdict(list)
    merged = defaultdict(list)
    citations = defaultdict(list)
    with open(args.turtle, "w") as turtle:
        with open(args.prologue) as prologue:
            turtle.write(prologue.read().replace("DATE", date.today().isoformat()))

        # TODO: ontology
        # TODO: annotation properties

        with zipfile.ZipFile(args.taxdmp) as taxdmp:
            with taxdmp.open("names.dmp") as dmp:
                for line in io.TextIOWrapper(dmp):
                    tax_id, name, unique, name_class, _ = split_line(line)
                    if name_class == "scientific name":
                        labels[tax_id] = name
                        scientific_names[name].append([tax_id, unique])
                    else:
                        synonyms[tax_id].append([name, unique, name_class])
                    if limit and int(tax_id) > limit:
                        break

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
                    cit_id, cit_key, pubmed_id, medline_id, url, text, tax_id_list, _ = split_line(line)
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
                    result = convert_node(node, labels[tax_id], merged[tax_id], synonyms[tax_id], citations[tax_id])
                    turtle.write(result)
                    if limit and int(tax_id) > limit:
                        break

            # TODO: delnodes
            # TODO: ranks


if __name__ == "__main__":
    main()
