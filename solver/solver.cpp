// Exhaustive tiling counter for 5-wide rectangles.
// stdin:
//   T                                   (piece types)
//   T lines: <char> <k> r1 c1 ... rk ck  (base shape)
//   J                                   (jobs)
//   J lines: <H> <m> t1 n1 ... tm nm     (type index, count)
// stdout, one line per job:
//   <fixed solutions> <solutions modulo symmetry> <sampleGrid grid or ->
// Search: depth-first, always cover the lowest-index empty cell, trying every
// remaining piece type in every rotation/reflection. Each tiling is reached
// exactly once. Pruning: every empty region must be at least as big as the
// smallest remaining piece and be a sum of remaining piece sizes (subset-sum).
#include <bits/stdc++.h>
using namespace std;
typedef unsigned long long u64;
const int W = 5;

struct Type { char id; vector<pair<int,int>> cells; vector<vector<pair<int,int>>> orients; };
vector<Type> types;
int H, NC;
u64 FULL, COLL, COLR;                 // masks: board, not-col0, not-col4
map<pair<int,int>, vector<vector<u64>>> cache; // (type,H) -> per anchor cell
vector<vector<u64>>* P[32];
int cnt[32], sz[32], tid[32], NT;
char grid[64];
long long fixedCount;
unordered_set<string> uniq;
string sampleGrid;

vector<vector<pair<int,int>>> orientations(vector<pair<int,int>> c) {
    set<vector<pair<int,int>>> out;
    for (int f = 0; f < 2; f++) {
        for (int r = 0; r < 4; r++) {
            for (auto& p : c) p = {p.second, -p.first};
            int mr = INT_MAX, mc = INT_MAX;
            for (auto& p : c) mr = min(mr, p.first), mc = min(mc, p.second);
            vector<pair<int,int>> n;
            for (auto& p : c) n.push_back({p.first - mr, p.second - mc});
            sort(n.begin(), n.end());
            out.insert(n);
        }
        for (auto& p : c) p.second = -p.second;
    }
    return vector<vector<pair<int,int>>>(out.begin(), out.end());
}

vector<vector<u64>>& placements(int t) {
    auto key = make_pair(t, H);
    auto it = cache.find(key);
    if (it != cache.end()) return it->second;
    vector<vector<u64>> v(NC);
    for (auto& o : types[t].orients)
        for (int r = 0; r < H; r++) for (int c = 0; c < W; c++) {
            u64 m = 0; bool ok = true;
            for (auto& p : o) {
                int rr = r + p.first, cc = c + p.second;
                if (rr >= H || cc >= W) { ok = false; break; }
                m |= 1ULL << (rr * W + cc);
            }
            if (ok) v[__builtin_ctzll(m)].push_back(m);
        }
    return cache[key] = v;
}

inline u64 grow(u64 m, u64 free_) {
    u64 g = m | ((m & COLR) << 1) | ((m & COLL) >> 1) | (m << W) | (m >> W);
    return g & free_;
}

bool regionsOk(u64 occ) {
    u64 fr = ~occ & FULL;
    // reachable sums of remaining piece sizes
    bitset<64> sums; sums[0] = 1; int minsz = 99;
    for (int t = 0; t < NT; t++) for (int k = 0; k < cnt[t]; k++) { sums |= sums << sz[t]; minsz = min(minsz, sz[t]); }
    while (fr) {
        u64 reg = fr & -fr, prev = 0;
        while (reg != prev) { prev = reg; reg = grow(reg, fr); }
        int s = __builtin_popcountll(reg);
        if (s < minsz || !sums[s]) return false;
        fr &= ~reg;
    }
    return true;
}

string transformGrid(int s) {          // s indexes symmetry group
    string out(NC, '?');
    for (int r = 0; r < H; r++) for (int c = 0; c < W; c++) {
        int rr, cc;
        switch (s) {
            case 0: rr = r; cc = c; break;
            case 1: rr = r; cc = W - 1 - c; break;
            case 2: rr = H - 1 - r; cc = c; break;
            case 3: rr = H - 1 - r; cc = W - 1 - c; break;
            case 4: rr = c; cc = r; break;                       // square only
            case 5: rr = W - 1 - c; cc = r; break;
            case 6: rr = c; cc = H - 1 - r; break;
            default: rr = W - 1 - c; cc = H - 1 - r; break;
        }
        out[rr * W + cc] = grid[r * W + c];
    }
    return out;
}

void record() {
    fixedCount++;
    int ns = (H == W) ? 8 : 4;
    string best;
    for (int s = 0; s < ns; s++) { string g = transformGrid(s); if (best.empty() || g < best) best = g; }
    if (uniq.insert(best).second && sampleGrid.empty()) sampleGrid = best;
}

void search(u64 occ, int left) {
    if (left == 0) { record(); return; }
    int cell = __builtin_ctzll(~occ);
    for (int t = 0; t < NT; t++) {
        if (!cnt[t]) continue;
        for (u64 m : (*P[t])[cell]) {
            if (m & occ) continue;
            u64 o2 = occ | m;
            cnt[t]--;
            if (left == 1 || regionsOk(o2)) {
                for (u64 x = m; x; x &= x - 1) grid[__builtin_ctzll(x)] = types[tid[t]].id;
                search(o2, left - 1);
            }
            cnt[t]++;
        }
    }
}

int main() {
    int T; cin >> T;
    types.resize(T);
    for (auto& t : types) {
        int k; cin >> t.id >> k;
        for (int i = 0; i < k; i++) { int r, c; cin >> r >> c; t.cells.push_back({r, c}); }
        t.orients = orientations(t.cells);
    }
    int J; cin >> J;
    for (int j = 0; j < J; j++) {
        int m; cin >> H >> m;
        NC = H * W; FULL = (NC == 64) ? ~0ULL : ((1ULL << NC) - 1);
        COLL = COLR = 0;
        for (int i = 0; i < NC; i++) { if (i % W != 0) COLL |= 1ULL << i; if (i % W != W - 1) COLR |= 1ULL << i; }
        NT = m; int left = 0;
        for (int i = 0; i < m; i++) {
            int t, n; cin >> t >> n;
            tid[i] = t; P[i] = &placements(t); cnt[i] = n;
            sz[i] = types[t].cells.size(); left += n;
        }
        fixedCount = 0; uniq.clear(); sampleGrid.clear();
        search(0, left);
        cout << fixedCount << " " << uniq.size() << " " << (sampleGrid.empty() ? "-" : sampleGrid) << "\n";
        cout.flush();
    }
}
