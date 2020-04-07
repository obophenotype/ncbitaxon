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



def convert_names(tax_id, names):
    output = []
    for name, unique, name_class in names:
        if name_class in predicates:
            predicate = predicates[name_class]
            synonym = name
            if unique != '':
                synonym = unique
            synonym = synonym.replace('"', '\\"')
            output.append(f"""
NCBITaxon:{tax_id} {predicate} "{synonym}" .
[ a owl:Axiom
; owl:annotatedSource NCBITaxon:{tax_id}
; owl:annotatedProperty {predicate}
; owl:annotatedTarget "{synonym}"
; oboInOwl:hasSynonymType "{name_class}"
] .""")
    return output


def convert_node(tax_id, parent_tax_id, rank, names):
    output = [f"NCBITaxon:{tax_id} a owl:Class"]
    if parent_tax_id and parent_tax_id != "" and parent_tax_id != tax_id:
        output.append(f"; rdfs:subClassOf NCBITaxon:{tax_id}")
    if rank and rank != "":
        rank = rank.replace(" ", "_")
        output.append(f"; ncbitaxon:has_rank NCBITaxon:{rank}")
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
    parser.add_argument("turtle",
            type=str,
            help="The output Turtle file to write")
    args = parser.parse_args()

    limit = 1e7 # highest tax_id is currently 2,725,057
    names = defaultdict(list)
    with open(args.turtle, "w") as turtle:
        with open(args.prologue) as prologue:
            turtle.write(prologue.read())

        with zipfile.ZipFile(args.taxdmp) as taxdmp:
            with taxdmp.open("names.dmp") as dmp:
                for line in io.TextIOWrapper(dmp):
                    tax_id, name, unique, name_class, _ = [x.strip() for x in line.split("|")]
                    names[tax_id].append([name, unique, name_class])
                    if int(tax_id) > limit:
                        break
            # TODO: citations
            with taxdmp.open("nodes.dmp") as dmp:
                for line in io.TextIOWrapper(dmp):
                    tax_id, parent_tax_id, rank, _ = [x.strip() for x in line.split("|", 3)]
                    result = convert_node(tax_id, parent_tax_id, rank, names[tax_id])
                    turtle.write(result)
                    if int(tax_id) > limit:
                        break
            # TODO: merged
            # TODO: delnodes


if __name__ == "__main__":
    main()
