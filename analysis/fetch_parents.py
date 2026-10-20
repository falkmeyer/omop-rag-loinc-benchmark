"""Fetch direct parents (LOINC multiaxial hierarchy) for all codes needed, via the public FHIR server tx.fhir.org."""
import sys, os, json, time, urllib.request, concurrent.futures as cf
import pandas as pd
B, CACHE = sys.argv[1], sys.argv[2]
d = pd.read_csv(os.path.join(B, "D_LABITEMS.csv")); d.columns = [c.lower() for c in d.columns]
codes = set(d.loinc_code.dropna().astype(str).str.strip())
rag = pd.read_csv(os.path.join(B, "data/result_3_formatted.csv"), on_bad_lines="skip")
for k in range(1, 6): codes |= set(rag[f"R{k}_LOINC"].dropna().astype(str).str.strip())
u = pd.read_csv(os.path.join(B, "data/final_mapping_usagi.csv"))
codes |= set(u.targetConceptCode.dropna().astype(str).str.strip())
codes = sorted(c for c in codes if c and c != "nan" and not c.startswith("LG"))
cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
todo = [c for c in codes if c not in cache]
print("codes:", len(codes), "cached:", len(cache), "todo:", len(todo), flush=True)

def get(code):
    url = f"https://tx.fhir.org/r4/CodeSystem/$lookup?system=http://loinc.org&code={code}&property=parent"
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/fhir+json", "User-Agent": "loinc-hierarchy-check/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
            parents = sorted({q.get("valueCode") for p in data.get("parameter", []) if p["name"] == "property"
                              for q in p["part"] if q["name"] == "value"
                              and any(x["name"] == "code" and x.get("valueCode") == "parent" for x in p["part"])})
            return code, {"found": True, "parents": parents}
        except urllib.error.HTTPError as e:
            if e.code in (400, 404, 422): return code, {"found": False, "parents": []}
            time.sleep(2 * (attempt + 1))
        except Exception:
            time.sleep(2 * (attempt + 1))
    return code, None

done = 0
with cf.ThreadPoolExecutor(4) as ex:
    for code, res in ex.map(get, todo):
        if res is not None: cache[code] = res
        done += 1
        if done % 200 == 0:
            json.dump(cache, open(CACHE, "w")); print(done, flush=True)
json.dump(cache, open(CACHE, "w"))
print("finished; cached", len(cache), "not found:", sum(not v["found"] for v in cache.values()),
      "failed:", len([c for c in codes if c not in cache]))
