// Exhaustive tiling counter for 5-wide rectangles. Go port of solver.cpp, same
// input, output and search order (so the sample grid is the same too).
// stdin:
//
//	T                                   (piece types)
//	T lines: <char> <k> r1 c1 ... rk ck  (base shape)
//	J                                   (jobs)
//	J lines: <H> <m> t1 n1 ... tm nm     (type index, count)
//
// stdout, one line per job:
//
//	<fixed solutions> <solutions modulo symmetry> <sampleGrid grid or ->
//
// Search: depth-first, always cover the lowest-index empty cell, trying every
// remaining piece type in every rotation/reflection. Each tiling is reached
// exactly once. Pruning: every empty region must be at least as big as the
// smallest remaining piece and be a sum of remaining piece sizes (subset-sum).
//
// Jobs are independent, so they run on all cores (-j to change); output stays
// in input order.
package main

import (
	"bufio"
	"flag"
	"fmt"
	"math/bits"
	"os"
	"runtime"
	"sort"
	"strconv"
)

const width = 5

type cell struct{ row, column int }

type pieceType struct {
	id           byte
	cells        []cell
	orientations [][]cell
}

type job struct {
	height      int
	typeIndices []int
	counts      []int
}

var types []pieceType

// orientations returns the distinct rotations/reflections of cells, normalised to
// (0,0) and sorted lexicographically, like std::set<vector<pair<int,int>>>.
func orientations(cells []cell) [][]cell {
	cells = append([]cell(nil), cells...)
	seen := map[string]bool{}
	var result [][]cell
	for flip := 0; flip < 2; flip++ {
		for rotation := 0; rotation < 4; rotation++ {
			for i := range cells {
				cells[i] = cell{cells[i].column, -cells[i].row}
			}
			minRow, minColumn := 1<<30, 1<<30
			for _, current := range cells {
				minRow, minColumn = min(minRow, current.row), min(minColumn, current.column)
			}
			normalized := make([]cell, len(cells))
			for i, current := range cells {
				normalized[i] = cell{current.row - minRow, current.column - minColumn}
			}
			sort.Slice(normalized, func(i, j int) bool { return less(normalized[i], normalized[j]) })
			if key := fmt.Sprint(normalized); !seen[key] {
				seen[key] = true
				result = append(result, normalized)
			}
		}
		for i := range cells {
			cells[i].column = -cells[i].column
		}
	}
	sort.Slice(result, func(i, j int) bool {
		first, second := result[i], result[j]
		for index := 0; index < len(first) && index < len(second); index++ {
			if first[index] != second[index] {
				return less(first[index], second[index])
			}
		}
		return len(first) < len(second)
	})
	return result
}

func less(first, second cell) bool {
	return first.row < second.row || (first.row == second.row && first.column < second.column)
}

// solver holds one worker's state; the placement cache is per worker.
type solver struct {
	cache map[[2]int][][]uint64 // (type, height) -> placements per anchor cell

	height, cellCount             int
	boardMask                     uint64
	notFirstColumn, notLastColumn uint64
	placements                    [][][]uint64 // per job piece: placements per anchor cell
	remaining, sizes, typeIndex   []int        // per job piece
	grid                          [64]byte
	fixedCount                    int64
	uniqueGrids                   map[string]struct{}
	sample                        string
}

func (s *solver) placementsFor(typeIndex int) [][]uint64 {
	key := [2]int{typeIndex, s.height}
	if cached, ok := s.cache[key]; ok {
		return cached
	}
	byAnchor := make([][]uint64, s.cellCount)
	for _, orientation := range types[typeIndex].orientations {
		for row := 0; row < s.height; row++ {
			for column := 0; column < width; column++ {
				var mask uint64
				ok := true
				for _, offset := range orientation {
					cellRow, cellColumn := row+offset.row, column+offset.column
					if cellRow >= s.height || cellColumn >= width {
						ok = false
						break
					}
					mask |= 1 << (cellRow*width + cellColumn)
				}
				if ok {
					anchor := bits.TrailingZeros64(mask)
					byAnchor[anchor] = append(byAnchor[anchor], mask)
				}
			}
		}
	}
	s.cache[key] = byAnchor
	return byAnchor
}

func (s *solver) grow(region, free uint64) uint64 {
	grown := region | (region&s.notLastColumn)<<1 | (region&s.notFirstColumn)>>1 | region<<width | region>>width
	return grown & free
}

func (s *solver) regionsOk(occupied uint64) bool {
	free := ^occupied & s.boardMask
	// reachable sums of remaining piece sizes
	var sums uint64 = 1
	smallest := 99
	for index := range s.remaining {
		for instance := 0; instance < s.remaining[index]; instance++ {
			sums |= sums << s.sizes[index]
			smallest = min(smallest, s.sizes[index])
		}
	}
	for free != 0 {
		region, previous := free&-free, uint64(0)
		for region != previous {
			previous = region
			region = s.grow(region, free)
		}
		size := bits.OnesCount64(region)
		if size < smallest || sums>>size&1 == 0 {
			return false
		}
		free &^= region
	}
	return true
}

func (s *solver) transformGrid(symmetry int) string {
	result := make([]byte, s.cellCount)
	for i := range result {
		result[i] = '?'
	}
	height := s.height
	for row := 0; row < height; row++ {
		for column := 0; column < width; column++ {
			var targetRow, targetColumn int
			switch symmetry {
			case 0:
				targetRow, targetColumn = row, column
			case 1:
				targetRow, targetColumn = row, width-1-column
			case 2:
				targetRow, targetColumn = height-1-row, column
			case 3:
				targetRow, targetColumn = height-1-row, width-1-column
			case 4: // square only
				targetRow, targetColumn = column, row
			case 5:
				targetRow, targetColumn = width-1-column, row
			case 6:
				targetRow, targetColumn = column, height-1-row
			default:
				targetRow, targetColumn = width-1-column, height-1-row
			}
			result[targetRow*width+targetColumn] = s.grid[row*width+column]
		}
	}
	return string(result)
}

func (s *solver) record() {
	s.fixedCount++
	symmetryCount := 4
	if s.height == width {
		symmetryCount = 8
	}
	best := ""
	for symmetry := 0; symmetry < symmetryCount; symmetry++ {
		if candidate := s.transformGrid(symmetry); best == "" || candidate < best {
			best = candidate
		}
	}
	if _, ok := s.uniqueGrids[best]; !ok {
		s.uniqueGrids[best] = struct{}{}
		if s.sample == "" {
			s.sample = best
		}
	}
}

func (s *solver) search(occupied uint64, piecesLeft int) {
	if piecesLeft == 0 {
		s.record()
		return
	}
	anchor := bits.TrailingZeros64(^occupied)
	for index := range s.remaining {
		if s.remaining[index] == 0 {
			continue
		}
		for _, mask := range s.placements[index][anchor] {
			if mask&occupied != 0 {
				continue
			}
			next := occupied | mask
			s.remaining[index]--
			if piecesLeft == 1 || s.regionsOk(next) {
				for cellBits := mask; cellBits != 0; cellBits &= cellBits - 1 {
					s.grid[bits.TrailingZeros64(cellBits)] = types[s.typeIndex[index]].id
				}
				s.search(next, piecesLeft-1)
			}
			s.remaining[index]++
		}
	}
}

func (s *solver) run(current job) string {
	s.height, s.cellCount = current.height, current.height*width
	if s.cellCount == 64 {
		s.boardMask = ^uint64(0)
	} else {
		s.boardMask = 1<<s.cellCount - 1
	}
	s.notFirstColumn, s.notLastColumn = 0, 0
	for i := 0; i < s.cellCount; i++ {
		if i%width != 0 {
			s.notFirstColumn |= 1 << i
		}
		if i%width != width-1 {
			s.notLastColumn |= 1 << i
		}
	}
	typeCount := len(current.typeIndices)
	s.placements = make([][][]uint64, typeCount)
	s.remaining, s.sizes, s.typeIndex = make([]int, typeCount), make([]int, typeCount), make([]int, typeCount)
	piecesLeft := 0
	for i, typeIndex := range current.typeIndices {
		s.typeIndex[i], s.placements[i], s.remaining[i] = typeIndex, s.placementsFor(typeIndex), current.counts[i]
		s.sizes[i] = len(types[typeIndex].cells)
		piecesLeft += current.counts[i]
	}
	s.fixedCount, s.uniqueGrids, s.sample = 0, map[string]struct{}{}, ""
	s.search(0, piecesLeft)
	sample := s.sample
	if sample == "" {
		sample = "-"
	}
	return fmt.Sprintf("%d %d %s", s.fixedCount, len(s.uniqueGrids), sample)
}

func main() {
	workers := flag.Int("j", runtime.NumCPU(), "parallel jobs")
	flag.Parse()

	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 1<<20), 1<<20)
	scanner.Split(bufio.ScanWords)
	readWord := func() string {
		if !scanner.Scan() {
			fmt.Fprintln(os.Stderr, "unexpected end of input")
			os.Exit(1)
		}
		return scanner.Text()
	}
	readInt := func() int {
		value, err := strconv.Atoi(readWord())
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		return value
	}

	types = make([]pieceType, readInt())
	for i := range types {
		piece := &types[i]
		piece.id = readWord()[0]
		cellCount := readInt()
		for index := 0; index < cellCount; index++ {
			row := readInt()
			piece.cells = append(piece.cells, cell{row, readInt()})
		}
		piece.orientations = orientations(piece.cells)
	}
	jobs := make([]job, readInt())
	for i := range jobs {
		current := &jobs[i]
		current.height = readInt()
		typeCount := readInt()
		for index := 0; index < typeCount; index++ {
			current.typeIndices = append(current.typeIndices, readInt())
			current.counts = append(current.counts, readInt())
		}
	}

	results := make([]chan string, len(jobs))
	for i := range results {
		results[i] = make(chan string, 1)
	}
	jobIndices := make(chan int)
	go func() {
		for i := range jobs {
			jobIndices <- i
		}
		close(jobIndices)
	}()
	for worker := 0; worker < max(1, *workers); worker++ {
		go func() {
			state := &solver{cache: map[[2]int][][]uint64{}}
			for i := range jobIndices {
				results[i] <- state.run(jobs[i])
			}
		}()
	}
	writer := bufio.NewWriter(os.Stdout)
	for _, result := range results {
		fmt.Fprintln(writer, <-result)
		writer.Flush()
	}
}
