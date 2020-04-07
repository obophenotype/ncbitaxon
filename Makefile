.PHONY: all
all: ncbitaxon.owl ncbitaxon.obo

.PHONY: clean
clean:
	rm -rf build

ROBOT := java -Xmx16g -jar bin/robot.jar

build/taxdmp.zip: | build
	curl -L -o $@ https://ftp.ncbi.nih.gov/pub/taxonomy/taxdmp.zip

ncbitaxon.ttl: src/ncbitaxon.py src/prologue.ttl build/taxdmp.zip
	python3 $^ $@

.PRECIOUS: ncbitaxon.owl
.PRECIOUS: ncbitaxon.obo
ncbitaxon.owl ncbitaxon.obo: ncbitaxon.ttl
	$(ROBOT) convert -i $< -o $@
