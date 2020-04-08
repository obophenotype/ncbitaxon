.PHONY: all
all: ncbitaxon.owl ncbitaxon.obo

.PHONY: clean
clean:
	rm -rf build

build:
	mkdir -p $@

ROBOT := java -Xmx16g -jar build/robot.jar
build/robot.jar: | build
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/mireot-rdfxml/lastSuccessfulBuild/artifact/bin/robot.jar
# curl -L -o $@ https://github.com/ontodev/robot/releases/download/v1.6.0/robot.jar

build/taxdmp.zip: | build
	curl -L -o $@ https://ftp.ncbi.nih.gov/pub/taxonomy/taxdmp.zip

ncbitaxon.ttl: src/ncbitaxon.py src/prologue.ttl build/taxdmp.zip
	python3 $^ $@

.PRECIOUS: ncbitaxon.owl
.PRECIOUS: ncbitaxon.obo
ncbitaxon.owl ncbitaxon.obo: ncbitaxon.ttl | build/robot.jar
	$(ROBOT) convert -i $< -o $@






### Build Nov2019 version for comparison

build/Nov2019:
	mkdir -p $@

build/Nov2019/taxonomy_original.dat: | build/Nov2019
	curl -L -o $@ http://ftp.ebi.ac.uk/pub/databases/taxonomy/taxonomy.dat

build/Nov2019/taxonomy.dat: build/Nov2019/taxonomy_original.dat
	sed /^MISSPELLING/d $< > $@

build/Nov2019/taxdmp.zip: | build/Nov2019
	curl -L -o $@ https://ftp.ncbi.nih.gov/pub/taxonomy/taxdump_archive/taxdmp_2019-11-01.zip

build/Nov2019/ncbi2owl: bin/ncbi2owl | build/Nov2019
	cp $< $@

build/Nov2019/ncbi2owl.jar: bin/ncbi2owl.jar | build/Nov2019
	cp $< $@

build/Nov2019/ncbitaxon.owl: build/Nov2019/ncbi2owl build/Nov2019/ncbi2owl.jar build/Nov2019/taxonomy.dat build/Nov2019/taxdmp.zip
	cd build/Nov2019 && NCBI_MEMORY=16G ./ncbi2owl -t

build/Nov2019/ncbitaxon_small.owl: src/extract_test.py build/Nov2019/ncbitaxon.owl taxa.txt
	python3 $^ $@

build/Nov2019/ncbitaxon_new.ttl: src/ncbitaxon.py src/prologue.ttl build/Nov2019/taxdmp.zip taxa.txt
	python3 $^ $@

build/Nov2019/ncbitaxon_new.owl: build/Nov2019/ncbitaxon_new.ttl
	$(ROBOT) convert -i $< -o $@

build/Nov2019/ncbitaxon_new_small.owl: src/extract_test.py build/Nov2019/ncbitaxon_new.owl taxa.txt
	python3 $^ $@

.PHONY:
build/Nov2019/ncbitaxon.diff: build/Nov2019/ncbitaxon_small.owl build/Nov2019/ncbitaxon_new_small.owl
	diff $^ > $@
# $(ROBOT) diff --left $(word 1,$^) --right $(word 2,$^) --output $@

test: build/Nov2019/ncbitaxon.diff
