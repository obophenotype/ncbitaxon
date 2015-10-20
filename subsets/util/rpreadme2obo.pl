#!/usr/bin/perl
while(<>) {
    last if (m@^Proteome_ID@);
}
print "ontology: ncbitaxon/subsets/rp\n";
print "synonymtypedef: ABBREVATION \"abbreviation\"\n";
print "\n";

open(F,">rpids.txt");
while(<>) {
    if (m@^(UP\d+)\s+(\d+)\s+(\S+)@) {
        my ($pid,$taxid,$code) = ($1,$2,$3);
        $taxid = "NCBITaxon:$taxid";
        print F "$taxid\n";
        print "[Term]\n";
        print "id: $taxid\n";
        print "xref: UniProtProteome:$pid\n";
        print "synonym: \"$code\" BROAD ABBREVIATION [UniProtProteome:$pid]\n" unless $code eq 'None';
        print "\n";
    }
    else {
        last;
    }
}
close(F);
