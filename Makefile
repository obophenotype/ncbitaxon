.PHONY: all
all: ncbitaxon.owl ncbitaxon.obo ncbitaxon.json ncbi_diff_latest_current_obo.txt ncbitaxon/ncbitaxon-minimal.owl
all: ncbitaxon.owl.gz ncbitaxon.obo.gz ncbitaxon.json.gz ncbitaxon/ncbitaxon-minimal.owl.gz

ROBOT=robot
DATE=$(shell date '+%Y-%m-01')
VARIANTDIR=ncbitaxon

# Per-target timing/memory log (mirrors ODK convention).
# Run with: ODK_DEBUG=yes ./odk.sh make <target>
# odk.sh sets ODK_DEBUG_FILE in the env to a single absolute path so
# this Makefile and subsets/Makefile both append to the same log.
SCRIPTSDIR = src/scripts
ifeq ($(ODK_DEBUG),yes)
SHELL = $(SCRIPTSDIR)/run-command.sh
endif

.PHONY: clean
clean:
	rm -rf build

build:
	mkdir -p $@

$(VARIANTDIR):
	mkdir -p $@

build/taxdmp.zip: | build
	curl -L -o $@ https://ftp.ncbi.nih.gov/pub/taxonomy/taxdump_archive/taxdmp_$(DATE).zip

ncbitaxon.ttl: src/ncbitaxon.py build/taxdmp.zip
	python3 $^ $@

ncbitaxon.%.gz: ncbitaxon.%
	gzip -c $< > $@.tmp && mv $@.tmp $@

.PRECIOUS: ncbitaxon.owl
.PRECIOUS: ncbitaxon.obo
.PRECIOUS: $(VARIANTDIR)/ncbitaxon-minimal.owl
ncbitaxon.owl ncbitaxon.obo ncbitaxon.json: ncbitaxon.ttl
	$(ROBOT) convert -i $< -o $@

$(VARIANTDIR)/ncbitaxon-minimal.owl: ncbitaxon.ttl src/queries/ncbitaxon-minimal.ru | $(VARIANTDIR)
	$(ROBOT) query --input $< --format xml --query $(word 2,$^) $@.tmp && mv $@.tmp $@

$(VARIANTDIR)/ncbitaxon-minimal.owl.gz: $(VARIANTDIR)/ncbitaxon-minimal.owl
	gzip -c $< > $@.tmp && mv $@.tmp $@

ncbi_diff_latest_current_%.txt: ncbitaxon.%
	wget http://purl.obolibrary.org/obo/ncbitaxon.$* -O current_ncbitaxon.$*
	$(ROBOT) diff --left current_ncbitaxon.$* --right ncbitaxon.$* -o $@

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

build/Nov2019/ncbitaxon_small.owl: src/extract_test.py build/Nov2019/ncbitaxon.owl taxa.tsv
	python3 $^ $@

build/Nov2019/ncbitaxon_new.ttl: src/ncbitaxon.py build/Nov2019/taxdmp.zip taxa.tsv
	python3 $^ $@

build/Nov2019/ncbitaxon_new.owl: build/Nov2019/ncbitaxon_new.ttl
	$(ROBOT) convert -i $< -o $@

build/Nov2019/ncbitaxon_new_small.owl: src/extract_test.py build/Nov2019/ncbitaxon_new.owl taxa.tsv
	python3 $^ $@

build/Nov2019/ncbitaxon.diff: build/Nov2019/ncbitaxon_small.owl build/Nov2019/ncbitaxon_new_small.owl
	-diff $^ > $@

build/Nov2019/ncbitaxon_robot.diff: build/Nov2019/ncbitaxon_small.owl build/Nov2019/ncbitaxon_new_small.owl
	$(ROBOT) diff --left $(word 1,$^) --right $(word 2,$^) --output $@

# This is helpful for finding syntax errors in the Turtle
build/ncbitaxon.owl: ncbitaxon.ttl
	rapper -i turtle ncbitaxon.ttl -o rdfxml > build/ncbitaxon.owl

.PHONY: test
test: build/Nov2019/ncbitaxon.diff build/Nov2019/ncbitaxon_robot.diff
