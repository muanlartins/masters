MAIN = main

.PHONY: all clean distclean open zip artifact-zip tables

all: $(MAIN).pdf

SRC = $(wildcard sections/*.tex) $(wildcard tables/*.tex) references.bib $(wildcard figures/*)

# Section 5's tables are generated from the artifact's measured JSON.
tables:
	$(MAKE) -C artifact tables verify

$(MAIN).pdf: $(MAIN).tex $(SRC)
	tectonic --synctex $(MAIN).tex

open: $(MAIN).pdf
	open $(MAIN).pdf

zip: clean
	rm -f $(MAIN).zip
	zip -r $(MAIN).zip . -x '$(MAIN).pdf' 'Makefile' '*.zip' '.DS_Store' 'readme.txt' 'history.txt' 'llncsdoc.pdf' '*_raw.txt' 'artifact/*' 'tmp/*' '*.md'
	@echo "$(MAIN).zip ready — upload to Overleaf via 'New Project > Upload Project'"

artifact-zip:
	rm -f edge-fusion-artifact.zip
	zip -r edge-fusion-artifact.zip artifact sections tables \
	  -x 'artifact/build/*' 'artifact/node_modules/*' 'artifact/.venv/*' 'artifact/__pycache__/*' \
	     'artifact/vfusion/__pycache__/*' 'artifact/scripts/__pycache__/*' 'artifact/.DS_Store'
	@echo "edge-fusion-artifact.zip ready — upload as supplementary material"

clean:
	rm -f *.aux *.log *.out *.bbl *.blg *.toc *.synctex.gz *.fdb_latexmk *.fls

distclean: clean
	rm -f $(MAIN).pdf
