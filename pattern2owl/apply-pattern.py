#!/usr/bin/env python3

__author__ = 'cjm'

import argparse
import logging
import re
import yaml
import json
import uuid
import csv


def main():

    parser = argparse.ArgumentParser(description='DOSDB'
                                                 'fooo',
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-t', '--to', type=str, required=False,
                        help='Renderer')
    parser.add_argument('-n', '--name', type=str, required=False, default='auto',
                        help='Ontology name')
    parser.add_argument('-b', '--base', type=str, required=False, default='http://purl.obolibrary.org/obo/',
                        help='URI base prefix')
    parser.add_argument('-p', '--pattern', type=str, required=False,
                        help='YAML Pattern file')
    parser.add_argument('-i', '--input', type=str, required=False,
                        help='Input file for values to be filled in template')
    parser.add_argument('-a', '--annotate', type=bool, required=False,
                        help='Annotate each generated class with template values')
    args = parser.parse_args()

    pattern_name = args.pattern
    f = open(args.pattern, 'r') 
    tobj = yaml.load(f)
    if 'pattern_name' not in tobj:
        tobj['pattern_name'] = pattern_name
    
    bindings_list = [{'imported': 'foo'}, {'imported': 'bar'}]
    if args.input:
        bindings_list = parse_bindings_list(args.input)
    print('Prefix: : <%s>' % args.base)
    print('Prefix: IAO: <http://purl.obolibrary.org/obo/IAO_>')
    print('Prefix: DOSDP: <http://geneontology.org/foo/>')
    print()
    print('AnnotationProperty: IAO:0000115')
    for v in tobj['vars']:
        print('AnnotationProperty: %s' % make_internal_annotation_property(tobj, v))
    print('AnnotationProperty: %s' % get_applies_pattern_property())
    ##print('AnnotationProperty: %s' % make_internal_annotation_property(tobj['pattern_name']))
    print('Ontology: <%s%s>' % (args.base, args.name))

    p = tobj
    # build map of quoted entity replacements
    qm = {}
    for k in p['classes']:
        iri = p['classes'][k]
        qm[k] = iri
        print('Class: %s ## %s' % (iri,k))
    for k in p['relations']:
        iri = p['relations'][k]
        qm[k] = iri
        print('ObjectProperty: %s ## %s' % (iri,k))

    print('## Auto-generated classes')
    for bindings in bindings_list:
        cls_iri = uuid_iri()
        if 'class_iri' in tobj:
            cls_iri = apply_template(tobj['class_iri'], bindings)
        if 'iri' in bindings:
            cls_iri = bindings['iri']
        apply_pattern(tobj, qm, bindings, cls_iri, args)
    
def uuid_iri():
    return format('urn:uuid:%s' % str(uuid.uuid4()))

def render_iri(iri):
    if iri.startswith("urn:") or iri.startswith("http"):
        return "<"+iri+">"
    return iri

def parse_bindings_list(fn):
    delimiter='\t'
    if fn.endswith("csv"):
        delimiter=','
    input_file = csv.DictReader(open(fn), delimiter=delimiter)
    bindings_list = [row for row in input_file]
    return bindings_list

def get_values(tobj, bindings, isLabel=False):
    lvars = tobj['vars']
    vals = []
    for v in lvars:
        varval = ""
        if isLabel:
            varval = bindings[v+" label"]
        else:
            varval = render_iri(bindings[v])
        vals.append(varval)
    return vals

def apply_template(tobj, bindings, isLabel=False):
    textt = tobj['text']
    vals = get_values(tobj, bindings, isLabel)
    text = format(textt % tuple(vals))
    return text

def apply_pattern(p, qm, bindings, cls_iri, args):
    print("")
    var_bindings = {}
    for v in p['vars']:
        iri = bindings[v]
        var_bindings[v] = iri
        vl = v + " label"
        lbl = bindings[vl] if vl in bindings else ''
        print('Class: %s ## %s' % (iri,lbl))

    print("## "+str(json.dumps(var_bindings)))

    print('Class: %s' % render_iri(cls_iri))
    if 'name' in p:
        tobj = p['name']
        text = apply_template(tobj, bindings, True)
        write_annotation('rdfs:label', text, bindings)
    if 'def' in p:
        tobj = p['def']
        text = apply_template(tobj, bindings, True)
        # todo: protect against special characters
        write_annotation('IAO:0000115', text, bindings)
    if 'annotations' in p:
        tanns = p['annotations']
        for tobj in tanns:
            ap = tobj['property']
            text = apply_template(tobj, bindings)
            # todo: protect against special characters
            write_annotation(ap, text, bindings)
    if 'equivalentTo' in p:
        tobj = p['equivalentTo']
        text = apply_template(tobj, bindings)
        cmt = text.replace("\n", "")
        expr = replace_quoted_entities(qm, text)
        print(' EquivalentTo: %s ## %s' % (expr,cmt))
    if 'subClassOf' in p:
        tobj = p['subClassOf']
        text = apply_template(tobj, bindings)
        expr = replace_quoted_entities(qm, text)
        print(' EquivalentTo: %s' % expr)
    if args.annotate:
        pn = p['pattern_name']
    
        print('  Annotations: %s "%s"' % (get_applies_pattern_property(), pn))
        for (k,v) in var_bindings.items():
            print('  Annotations: %s %s' % (make_internal_annotation_property(p, k), v))

def get_applies_pattern_property():
    return 'DOSDP:applies-pattern'
    
def make_internal_annotation_property(p, s):
    return p['pattern_name'] + "/"+s

def write_annotation(ap, text, bindings={}):
    if ap in bindings:
        # override
        if bindings[ap] != '':
            text = bindings[ap]

    # todo: allow non-literal annotations
    print(' Annotations: %s %s' % (ap,safe_quote(text)))

def safe_quote(text):
    text = text.replace("\n"," ").replace('"','\\"')
    return format('"%s"' % text)

# Stolen from DOS' code
def replace_quoted_entities(qm, text):
    for k in qm:
        v = qm[k]
        text = re.sub("\'"+k+"\'", v, text)  # Suspect this not Pythonic. Could probably be done with a fancy map lambda combo.  
    return text



if __name__ == "__main__":
    main()
