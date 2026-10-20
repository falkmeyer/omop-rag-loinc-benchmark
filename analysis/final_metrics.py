"""Recompute all results of the MIE 2027 paper from the raw outputs in Tom McCaughey's evaluation repository.

Corrections relative to the thesis evaluation:
  * reference codes and Usagi/RAG pairing are keyed by D_LABITEMS ITEMID (not by label), because labels repeat;
  * L1 is strict code identity (no normalisation table);
  * L2/L3 use direct parents of the LOINC multiaxial hierarchy (LOINC 2.82, fetched by fetch_parents.py).

Usage: python final_metrics.py <evaluation-repo> <parents_cache.json>
"""
import json
import os
import sys
from collections import Counter

import pandas as pd
from scipy.stats import chi2

B, CACHE = sys.argv[1], sys.argv[2]
PAR = {k: set(v["parents"]) for k, v in json.load(open(CACHE)).items()}

d = pd.read_csv(os.path.join(B, "D_LABITEMS.csv"))
d.columns = [c.lower() for c in d.columns]


def enh(r):
    p = [str(r.label).strip()]
    if pd.notna(r.fluid):
        p.append(f"in {str(r.fluid).strip()}")
    if pd.notna(r.category):
        p.append(f"{str(r.category).strip()} measurement")
    return " ".join(p)


d["enh"] = d.apply(enh, axis=1)
D = d.set_index("itemid")
GT = D.loinc_code.dropna().astype(str).str.strip()

rag = pd.read_csv(os.path.join(B, "data/result_3_formatted.csv"), on_bad_lines="skip")
rag = rag.merge(d[["itemid", "enh"]], left_on="EHR_Item", right_on="enh").set_index("itemid")
CAND = {i: [str(rag.at[i, f"R{k}_LOINC"]).strip() for k in range(1, 6)] for i in rag.index}
rr = pd.read_csv(os.path.join(B, "reranking_experiment2/reranked_formatted_v2.csv"))
rr = rr.merge(d[["itemid", "enh"]], left_on="EHR_Item", right_on="enh").set_index("itemid")
usagi = pd.read_csv(os.path.join(B, "data/final_mapping_usagi.csv"))
assert (usagi.groupby("sourceName").targetConceptCode.nunique() <= 1).all()
UPRED = D.label.map(usagi.groupby("sourceName").targetConceptCode.first().astype(str).str.strip())

IDS = sorted(i for i in rag.index if i in GT.index)          # pipeline items with reference code
UIDS = sorted(GT.index)                                       # Usagi items with reference code


def reranked(i):
    """Candidate list after reranking: chosen candidate to rank 1, others keep order (fallback: unchanged)."""
    c = CAND[i]
    if i not in rr.index:
        return c, False
    ch = int(rr.at[i, "llm_rank"]) - 1
    return [c[ch]] + c[:ch] + c[ch + 1:], True


def match(c, y, level):
    if c == y:
        return True
    if level >= 2 and c in PAR.get(y, set()):
        return True
    if level >= 3 and PAR.get(c, set()) & PAR.get(y, set()):
        return True
    return False


def first_rank(cands, y, level):
    return next((k + 1 for k, c in enumerate(cands) if match(c, y, level)), None)


def mcnemar(a, b):
    ao, bo = sum(x and not y for x, y in zip(a, b)), sum(y and not x for x, y in zip(a, b))
    both, nei = sum(x and y for x, y in zip(a, b)), sum(not x and not y for x, y in zip(a, b))
    p = chi2.sf((abs(ao - bo) - 1) ** 2 / (ao + bo), 1) if ao + bo else 1.0
    return both, ao, bo, nei, p


pct = lambda k, n: f"{k} ({100 * k / n:.1f}%)"
out = {}
print(f"Pipeline items with reference: {len(IDS)}; Usagi items: {len(UIDS)}; reranked: {sum(i in rr.index for i in IDS)}")
missing = [i for i in GT.index if not any(p for p in [PAR.get(GT[i])])]
print(f"reference codes without hierarchy entry: {sum(GT[i] not in PAR for i in GT.index)}")

# composition of retrieved candidates
kind = lambda c: "LP" if c.startswith("LP") else "LG" if c.startswith("LG") else "LOINC"
print("retrieval top-1 kinds:", Counter(kind(CAND[i][0]) for i in IDS))
print("retrieval top-5 kinds:", Counter(kind(c) for i in IDS for c in CAND[i]))
print("reranked top-1 kinds:", Counter(kind(reranked(i)[0][0]) for i in IDS))
print("items with >=1 standard LOINC (non-LP/LG) candidate in top-5:", sum(any(kind(c) == "LOINC" for c in CAND[i]) for i in IDS))
print("LLM choice distribution:", Counter(int(rr.at[i, "llm_rank"]) for i in IDS if i in rr.index))

for L in (1, 2, 3):
    n = len(IDS)
    r_rank = {i: first_rank(CAND[i], GT[i], L) for i in IDS}
    p_rank = {i: first_rank(reranked(i)[0], GT[i], L) for i in IDS}
    ret = {k: sum(1 for i in IDS if r_rank[i] and r_rank[i] <= k) for k in (1, 3, 5)}
    pip = {k: sum(1 for i in IDS if p_rank[i] and p_rank[i] <= k) for k in (1, 3, 5)}
    us_all = sum(match(UPRED[i], GT[i], L) for i in UIDS)
    print(f"\n=== Level {L} ===")
    print(f"retrieval  n={n}: Top-1 {pct(ret[1], n)}  Top-3 {pct(ret[3], n)}  Top-5 {pct(ret[5], n)}")
    print(f"pipeline   n={n}: Top-1 {pct(pip[1], n)}  Top-3 {pct(pip[3], n)}")
    print(f"Usagi      n={len(UIDS)}: Top-1 {pct(us_all, len(UIDS))}")
    u1 = [match(UPRED[i], GT[i], L) for i in IDS]
    r1 = [r_rank[i] == 1 for i in IDS]
    p1 = [p_rank[i] == 1 for i in IDS]
    for name, a, b in (("Usagi vs retrieval", u1, r1), ("retrieval vs reranked", r1, p1), ("Usagi vs pipeline", u1, p1)):
        both, ao, bo, nei, p = mcnemar(a, b)
        print(f"  {name:22s} A={sum(a)} ({100*sum(a)/n:.1f}%) B={sum(b)} ({100*sum(b)/n:.1f}%) "
              f"both={both} A_only={ao} B_only={bo} neither={nei} diff={100*(sum(b)-sum(a))/n:+.1f}pp p={p:.2g}")
    # rank movements (only items actually reranked and with a correct candidate)
    imp = wor = same = 0
    by_orig = Counter(); demoted_from_1 = 0
    for i in IDS:
        if i not in rr.index or r_rank[i] is None:
            continue
        a, b = r_rank[i], p_rank[i]
        by_orig[(a, "imp" if b < a else "wor" if b > a else "same")] += 1
        imp += b < a; wor += b > a; same += b == a
    print(f"  movement (reranked items with correct candidate): improved {imp}, same {same}, worsened {wor}")
    for k in range(1, 6):
        tot = sum(v for (o, _), v in by_orig.items() if o == k)
        if tot:
            print(f"    orig rank {k}: n={tot} improved {by_orig[(k,'imp')]} ({100*by_orig[(k,'imp')]/tot:.0f}%) "
                  f"worsened {by_orig[(k,'wor')]} ({100*by_orig[(k,'wor')]/tot:.0f}%)")
    worsened = [i for i in IDS if i in rr.index and r_rank[i] and p_rank[i] > r_rank[i]]
    gen = sum("general" in str(rr.at[i, "llm_reason"]).lower() for i in worsened)
    print(f"  worsened items whose rationale mentions 'general': {gen}/{len(worsened)}")
    # complementarity: Usagi-correct items not in retrieval top-5; union coverage
    u_only_top1 = [i for i, a, b in zip(IDS, u1, r1) if a and not b]
    absent = [i for i in u_only_top1 if not (r_rank[i] and r_rank[i] <= 5)]
    union = sum(1 for i, a in zip(IDS, u1) if a or (r_rank[i] and r_rank[i] <= 5))
    print(f"  Usagi-only vs retrieval top-1: {len(u_only_top1)}, of which absent from top-5: {len(absent)} "
          f"(categories {Counter(D.at[i,'category'] for i in absent)}); labels e.g. {[D.at[i,'label'] for i in absent[:10]]}")
    print(f"  union retrieval top-5 + Usagi: {pct(union, n)}")
    # per category
    for cat in ("Hematology", "Chemistry", "Blood Gas"):
        ci = [k for k, i in enumerate(IDS) if D.at[i, "category"] == cat]
        if ci:
            print(f"  {cat:10s} n={len(ci)} Usagi {100*sum(u1[k] for k in ci)/len(ci):.1f}% "
                  f"retrieval {100*sum(r1[k] for k in ci)/len(ci):.1f}% pipeline {100*sum(p1[k] for k in ci)/len(ci):.1f}%")
