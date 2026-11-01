PY ?= python3

.PHONY: all solver solver-go data site stl cards clean
all: site

solver: build/solver
build/solver: solver/solver.cpp
	mkdir -p build
	g++ -O2 -o build/solver solver/solver.cpp

# Go port: same input, output and search order; runs jobs on all cores (-j N to change).
solver-go: build/solver-go
build/solver-go: solver/solver.go
	mkdir -p build
	go build -o build/solver-go solver/solver.go

# Recompute the analysis (box: ~10 min, full 12-pentomino set: under an hour, one core).
data: build/solver build/solver-go
	$(PY) analysis/katamino.py --set box
	$(PY) analysis/katamino.py --set full
	$(PY) analysis/forgiveness.py

site:
	$(PY) site/build_site.py

# Printable two-player card deck (PDF via headless Chrome or Edge)
cards:
	$(PY) cards/make_cards.py

# 3D-printable pieces and boards (needs: pip install numpy manifold3d)
stl:
	$(PY) print3d/make_stl.py

clean:
	rm -rf build
