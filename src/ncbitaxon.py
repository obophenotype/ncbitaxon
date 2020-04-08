#!/usr/bin/env python3

import argparse
import io
import zipfile

from collections import defaultdict


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

def convert_names(tax_id, names):
    output = []
    for name, unique, name_class in names:
        if name_class == "scientific name":
            synonym = name
            if unique != '':
                synonym = unique
            synonym = synonym.replace('"', '\\"')
            output.append(f"""
NCBITaxon:{tax_id} rdfs:label "{synonym}"^^xsd:string .""")
        elif name_class in predicates:
            synonym = name.replace('"', '\\"')
            predicate = predicates[name_class]
            synonym_type = name_class.replace(" ", "_")
            output.append(f"""
NCBITaxon:{tax_id} {predicate} "{synonym}"^^xsd:string .
[ a owl:Axiom
; owl:annotatedSource NCBITaxon:{tax_id}
; owl:annotatedProperty {predicate}
; owl:annotatedTarget "{synonym}"^^xsd:string
; oboInOwl:hasSynonymType ncbitaxon:{synonym_type}
] .""")
    return output


def convert_node(node, merged, names):
    tax_id = node["tax_id"]
    output = [f"NCBITaxon:{tax_id} a owl:Class"]

    parent_tax_id = node["parent_tax_id"]
    if parent_tax_id and parent_tax_id != "" and parent_tax_id != tax_id:
        output.append(f"; rdfs:subClassOf NCBITaxon:{parent_tax_id}")

    # TODO: cohort, subcohort
    rank = node["rank"]
    if rank and rank != "" and rank != "no rank":
        rank = rank.replace(" ", "_")
        output.append(f"; ncbitaxon:has_rank NCBITaxon:{rank}")
    
    for merge in merged:
        output.append(f'; oboInOwl:hasAlternativeId "NCBITaxon:{merge}"^^xsd:string')

    gc_id = node["genetic_code_id"]
    if gc_id:
        output.append(f'; oboInOwl:hasDbXref "GC_ID:{gc_id}"^^xsd:string')

    output.append('; oboInOwl:hasOBONamespace "ncbi_taxonomy"^^xsd:string')
    output.append(".")

    output += convert_names(tax_id, names)

    return "\n".join(output)


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
                taxa.add(line.strip())

    names = defaultdict(list)
    merged = defaultdict(list)
    with open(args.turtle, "w") as turtle:
        with open(args.prologue) as prologue:
            turtle.write(prologue.read())

        with zipfile.ZipFile(args.taxdmp) as taxdmp:
            with taxdmp.open("names.dmp") as dmp:
                for line in io.TextIOWrapper(dmp):
                    tax_id, name, unique, name_class, _ = [x.strip() for x in line.split("|")]
                    if taxa and tax_id in taxa:
                        names[tax_id].append([name, unique, name_class])
                    if limit and int(tax_id) > limit:
                        break

            with taxdmp.open("merged.dmp") as dmp:
                for line in io.TextIOWrapper(dmp):
                    old_tax_id, new_tax_id, _ = [x.strip() for x in line.split("|")]
                    if taxa and new_tax_id in taxa:
                        merged[new_tax_id].append(old_tax_id)

            # TODO: citations

            with taxdmp.open("nodes.dmp") as dmp:
                for line in io.TextIOWrapper(dmp):
                    node = {}
                    fields = [x.strip() for x in line.split("|")]
                    for i in range(0, min(len(fields), len(nodes_fields))):
                        node[nodes_fields[i]] = fields[i]
                    tax_id = node["tax_id"]
                    if taxa and tax_id in taxa:
                        result = convert_node(node, merged[tax_id], names[tax_id])
                        turtle.write(result)
                    if limit and int(tax_id) > limit:
                        break
            # TODO: merged
            # TODO: delnodes


if __name__ == "__main__":
    main()
