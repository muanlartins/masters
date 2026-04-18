MAIN = samplepaper

.PHONY: all clean distclean open zip

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex
	tectonic --synctex $(MAIN).tex

open: $(MAIN).pdf
	open $(MAIN).pdf

zip: clean
	rm -f $(MAIN).zip
	zip -r $(MAIN).zip . -x '$(MAIN).pdf' 'Makefile' '*.zip' '.DS_Store' 'readme.txt' 'history.txt' 'llncsdoc.pdf' '*_raw.txt'
	@echo "$(MAIN).zip ready — upload to Overleaf via 'New Project > Upload Project'"

clean:
	rm -f *.aux *.log *.out *.bbl *.blg *.toc *.synctex.gz *.fdb_latexmk *.fls

distclean: clean
	rm -f $(MAIN).pdf