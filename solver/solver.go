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

const W = 5

type cell struct{ r, c int }

type pieceType struct {
	id      byte
	cells   []cell
	orients [][]cell
}

type job struct {
	h      int
	tids   []int
	counts []int
}

var types []pieceType

// orientations returns the distinct rotations/reflections of c, normalised to
// (0,0) and sorted lexicographically, like std::set<vector<pair<int,int>>>.
func orientations(c []cell) [][]cell {
	c = append([]cell(nil), c...)
	seen := map[string]bool{}
	var out [][]cell
	for f := 0; f < 2; f++ {
		for r := 0; r < 4; r++ {
			for i := range c {
				c[i] = cell{c[i].c, -c[i].r}
			}
			mr, mc := 1<<30, 1<<30
			for _, p := range c {
				mr, mc = min(mr, p.r), min(mc, p.c)
			}
			n := make([]cell, len(c))
			for i, p := range c {
				n[i] = cell{p.r - mr, p.c - mc}
			}
			sort.Slice(n, func(i, j int) bool { return less(n[i], n[j]) })
			if k := fmt.Sprint(n); !seen[k] {
				seen[k] = true
				out = append(out, n)
			}
		}
		for i := range c {
			c[i].c = -c[i].c
		}
	}
	sort.Slice(out, func(i, j int) bool {
		a, b := out[i], out[j]
		for k := 0; k < len(a) && k < len(b); k++ {
			if a[k] != b[k] {
				return less(a[k], b[k])
			}
		}
		return len(a) < len(b)
	})
	return out
}

func less(a, b cell) bool { return a.r < b.r || (a.r == b.r && a.c < b.c) }

// solver holds one worker's state; the placement cache is per worker.
type solver struct {
	cache map[[2]int][][]uint64 // (type, H) -> placements per anchor cell

	h, nc            int
	full, coll, colr uint64
	p                [][][]uint64
	cnt, sz, tid     []int
	grid             [64]byte
	fixed            int64
	uniq             map[string]struct{}
	sample           string
}

func (s *solver) placements(t int) [][]uint64 {
	key := [2]int{t, s.h}
	if v, ok := s.cache[key]; ok {
		return v
	}
	v := make([][]uint64, s.nc)
	for _, o := range types[t].orients {
		for r := 0; r < s.h; r++ {
			for c := 0; c < W; c++ {
				var m uint64
				ok := true
				for _, p := range o {
					rr, cc := r+p.r, c+p.c
					if rr >= s.h || cc >= W {
						ok = false
						break
					}
					m |= 1 << (rr*W + cc)
				}
				if ok {
					a := bits.TrailingZeros64(m)
					v[a] = append(v[a], m)
				}
			}
		}
	}
	s.cache[key] = v
	return v
}

func (s *solver) grow(m, free uint64) uint64 {
	g := m | (m&s.colr)<<1 | (m&s.coll)>>1 | m<<W | m>>W
	return g & free
}

func (s *solver) regionsOk(occ uint64) bool {
	fr := ^occ & s.full
	// reachable sums of remaining piece sizes
	var sums uint64 = 1
	minsz := 99
	for t := range s.cnt {
		for k := 0; k < s.cnt[t]; k++ {
			sums |= sums << s.sz[t]
			minsz = min(minsz, s.sz[t])
		}
	}
	for fr != 0 {
		reg, prev := fr&-fr, uint64(0)
		for reg != prev {
			prev = reg
			reg = s.grow(reg, fr)
		}
		n := bits.OnesCount64(reg)
		if n < minsz || sums>>n&1 == 0 {
			return false
		}
		fr &^= reg
	}
	return true
}

func (s *solver) transformGrid(sym int) string {
	out := make([]byte, s.nc)
	for i := range out {
		out[i] = '?'
	}
	h := s.h
	for r := 0; r < h; r++ {
		for c := 0; c < W; c++ {
			var rr, cc int
			switch sym {
			case 0:
				rr, cc = r, c
			case 1:
				rr, cc = r, W-1-c
			case 2:
				rr, cc = h-1-r, c
			case 3:
				rr, cc = h-1-r, W-1-c
			case 4: // square only
				rr, cc = c, r
			case 5:
				rr, cc = W-1-c, r
			case 6:
				rr, cc = c, h-1-r
			default:
				rr, cc = W-1-c, h-1-r
			}
			out[rr*W+cc] = s.grid[r*W+c]
		}
	}
	return string(out)
}

func (s *solver) record() {
	s.fixed++
	ns := 4
	if s.h == W {
		ns = 8
	}
	best := ""
	for sym := 0; sym < ns; sym++ {
		if g := s.transformGrid(sym); best == "" || g < best {
			best = g
		}
	}
	if _, ok := s.uniq[best]; !ok {
		s.uniq[best] = struct{}{}
		if s.sample == "" {
			s.sample = best
		}
	}
}

func (s *solver) search(occ uint64, left int) {
	if left == 0 {
		s.record()
		return
	}
	cell := bits.TrailingZeros64(^occ)
	for t := range s.cnt {
		if s.cnt[t] == 0 {
			continue
		}
		for _, m := range s.p[t][cell] {
			if m&occ != 0 {
				continue
			}
			o2 := occ | m
			s.cnt[t]--
			if left == 1 || s.regionsOk(o2) {
				for x := m; x != 0; x &= x - 1 {
					s.grid[bits.TrailingZeros64(x)] = types[s.tid[t]].id
				}
				s.search(o2, left-1)
			}
			s.cnt[t]++
		}
	}
}

func (s *solver) run(j job) string {
	s.h, s.nc = j.h, j.h*W
	if s.nc == 64 {
		s.full = ^uint64(0)
	} else {
		s.full = 1<<s.nc - 1
	}
	s.coll, s.colr = 0, 0
	for i := 0; i < s.nc; i++ {
		if i%W != 0 {
			s.coll |= 1 << i
		}
		if i%W != W-1 {
			s.colr |= 1 << i
		}
	}
	m := len(j.tids)
	s.p, s.cnt, s.sz, s.tid = make([][][]uint64, m), make([]int, m), make([]int, m), make([]int, m)
	left := 0
	for i, t := range j.tids {
		s.tid[i], s.p[i], s.cnt[i] = t, s.placements(t), j.counts[i]
		s.sz[i] = len(types[t].cells)
		left += j.counts[i]
	}
	s.fixed, s.uniq, s.sample = 0, map[string]struct{}{}, ""
	s.search(0, left)
	sample := s.sample
	if sample == "" {
		sample = "-"
	}
	return fmt.Sprintf("%d %d %s", s.fixed, len(s.uniq), sample)
}

func main() {
	workers := flag.Int("j", runtime.NumCPU(), "parallel jobs")
	flag.Parse()

	in := bufio.NewScanner(os.Stdin)
	in.Buffer(make([]byte, 1<<20), 1<<20)
	in.Split(bufio.ScanWords)
	word := func() string {
		if !in.Scan() {
			fmt.Fprintln(os.Stderr, "unexpected end of input")
			os.Exit(1)
		}
		return in.Text()
	}
	num := func() int {
		n, err := strconv.Atoi(word())
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		return n
	}

	types = make([]pieceType, num())
	for i := range types {
		t := &types[i]
		t.id = word()[0]
		k := num()
		for c := 0; c < k; c++ {
			r := num()
			t.cells = append(t.cells, cell{r, num()})
		}
		t.orients = orientations(t.cells)
	}
	jobs := make([]job, num())
	for i := range jobs {
		j := &jobs[i]
		j.h = num()
		m := num()
		for k := 0; k < m; k++ {
			j.tids = append(j.tids, num())
			j.counts = append(j.counts, num())
		}
	}

	results := make([]chan string, len(jobs))
	for i := range results {
		results[i] = make(chan string, 1)
	}
	next := make(chan int)
	go func() {
		for i := range jobs {
			next <- i
		}
		close(next)
	}()
	for w := 0; w < max(1, *workers); w++ {
		go func() {
			s := &solver{cache: map[[2]int][][]uint64{}}
			for i := range next {
				results[i] <- s.run(jobs[i])
			}
		}()
	}
	out := bufio.NewWriter(os.Stdout)
	for _, r := range results {
		fmt.Fprintln(out, <-r)
		out.Flush()
	}
}
