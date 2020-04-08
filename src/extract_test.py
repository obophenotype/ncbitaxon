#!/usr/bin/env python3

import argparse
import re

def main():
    parser = argparse.ArgumentParser(
            description="Exract selected stanzas from ncbitaxon.owl")
    parser.add_argument("input",
            type=str,
            help="The input ncbitaxon.owl file")
    parser.add_argument("taxa",
            type=str,
            help="The file listing taxa to extract")
    parser.add_argument("output",
            type=str,
            help="The output OWL file")
    args = parser.parse_args()

    taxa = set()
    with open(args.taxa) as taxalist:
        for line in taxalist:
            taxa.add(line.strip())

    digits = re.compile(r'\d+')
    with open(args.output, "w") as output:
        with open(args.input) as ncbitaxon:
            keep = True
            post_rank = False
            skip_to_end = False
            for line in ncbitaxon:
                # Skip over merged annotations
                if "</rdf:RDF>" in line:
                    skip_to_end = False
                if skip_to_end:
                    continue
                if "<!-- http://purl.obolibrary.org/obo/NCBITaxon#_taxonomic_rank -->" in line:
                    post_rank = True
                if post_rank and "</owl:Class>" in line:
                    skip_to_end = True

                if "<!-- http://purl.obolibrary.org/obo/NCBITaxon_" in line:
                    matches = digits.search(line)
                    if not matches:
                        keep = True
                    elif matches[0] in taxa:
                        keep = True
                    else:
                        keep = False
                if keep:
                    output.write(line)


if __name__ == "__main__":
    main()
