"""Memory: each oracle's ψ vault read against its own sessions, in the same vector space.

    RELIC4_ROOT=~/relic4-fresh uv run --project ../agent-relic-v4 python report/memory.py   -> ~/.relic-extract/report/memory.json

For every oracle with both a vault (vaults.py) and main-session prompts:
  recall   share of its prompts whose nearest note in its own vault is within cosine 0.80 ("the vault knows this")
  unasked  share of its notes with no prompt of its own within 0.80 ("written, never asked about")
  writing  notes per month by section (memory/learnings, retrospectives, inbox, …) next to its prompts per month
Plus, over all vaults: notes written per month by section, and the sections' share of the whole.
Samples: up to 1,500 prompts and 1,500 notes per oracle, fixed seed.
"""

import glob
import json
import os
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

import common

HOME = Path.home()
OUT = HOME / ".relic-extract" / "report"
ROOT = Path(os.environ.get("RELIC4_ROOT", HOME / "relic4-fresh")).expanduser()
NEAR = 0.80


def unit(a):
    return a / (np.linalg.norm(a, axis=-1, keepdims=True) + 1e-9)


def top_section(sec):
    parts = (sec or "").split("/")
    return "/".join(parts[:2]) if parts[0] == "memory" else parts[0] or "(root)"


def main():
    t0 = time.time()
    con = common.connect(HOME / ".relic-scan", HOME / ".relic-extract")
    vdir = sorted(glob.glob(str(ROOT / "vec/_cache/unsloth--embeddinggemma-300m@*")))[0]
    con.execute(f"create view notes as select * from read_parquet('{HOME / '.relic-extract/vault/notes.parquet'}')")
    con.execute("""create table pk as select ses.cat, x.key, substr(x.ts_th, 1, 7) m from x join ses using (sid)
                   where x.role = 'user' and x.chunk = 0 and x.tier = 'main' and x.ts_th <> ''""")
    con.execute("create table nk as select cat, key, month m, section, vault from notes where chunk = 0")
    cats = [r[0] for r in con.execute("""select cat from (select cat, count(*) n from pk group by 1) p
                                         where cat in (select distinct cat from nk) and n >= 100 order by n desc limit 40""").fetchall()]
    con.execute("create temp table want as select distinct key from (select key from pk where cat in (select unnest(?::varchar[])) "
                "union select key from nk where cat in (select unnest(?::varchar[])))", [cats, cats])
    kv = con.sql(f"""select key, any_value(vector) AS vector from read_parquet('{vdir}/*.parquet')
                    where key in (select key from want) group by key order by key""").to_arrow_table()
    vec = kv.column("vector").combine_chunks()
    V = unit(vec.flatten().to_numpy(zero_copy_only=False).astype(np.float32).reshape(len(vec), -1))
    kix = {k: i for i, k in enumerate(kv.column("key").to_pylist())}
    print(f"memory: {len(cats)} oracles with a vault and prompts · {len(kix):,} vectors · {time.time() - t0:.0f}s")
    rng = np.random.default_rng(0)
    months = [r[0] for r in con.execute("select distinct m from pk order by 1").fetchall()]
    mi = {m: i for i, m in enumerate(months)}
    oracles = []
    for cat in cats:
        pks = sorted({kix[k] for k, in con.execute("select key from pk where cat = ?", [cat]).fetchall() if k in kix})
        nrows = con.execute("select key, m, section from nk where cat = ?", [cat]).fetchall()
        nks = sorted({kix[k] for k, _, _ in nrows if k in kix})
        if len(pks) < 50 or len(nks) < 10:
            continue
        P = V[rng.choice(pks, size=min(1500, len(pks)), replace=False)]
        N = V[rng.choice(nks, size=min(1500, len(nks)), replace=False)]
        S = P @ N.T
        recall = float((S.max(1) >= NEAR).mean())
        Nall, Pall = V[nks], V[pks]
        unasked = float(((N @ Pall.T).max(1) < NEAR).mean())
        secs = Counter(top_section(s) for _, _, s in nrows)
        writing = defaultdict(lambda: [0] * len(months))
        for _, m, s in nrows:
            if m in mi:
                writing[top_section(s)][mi[m]] += 1
        pm = [0] * len(months)
        for m, n in con.execute("select m, count(*) from pk where cat = ? group by 1", [cat]).fetchall():
            pm[mi[m]] = n
        oracles.append(dict(name=cat, prompts=len(pks), notes=len(nrows), distinct_notes=len(nks), recall=round(recall, 4),
                            unasked=round(unasked, 4), sections=secs.most_common(8),
                            learnings=secs.get("memory/learnings", 0), retros=secs.get("memory/retrospectives", 0),
                            prompts_by_month=pm, notes_by_month={k: v for k, v in writing.items() if sum(v)}))
    oracles.sort(key=lambda o: -o["prompts"])
    allsec = Counter()
    by_month = defaultdict(lambda: [0] * len(months))
    for sec, m, n in con.execute("select section, m, count(*) from nk where vault <> 'worktree' group by all").fetchall():
        allsec[top_section(sec)] += n
        if m in mi:
            by_month[top_section(sec)][mi[m]] += n
    keep = [s for s, _ in allsec.most_common(7)]
    other = [sum(v[i] for s, v in by_month.items() if s not in keep) for i in range(len(months))]
    out = dict(built=time.strftime("%Y-%m-%d %H:%M"), months=months, near=NEAR, oracles=oracles,
               sections=allsec.most_common(12), notes_by_month={**{s: by_month[s] for s in keep}, "other": other},
               totals=dict(notes=sum(allsec.values()), vaults=con.execute("select count(distinct cat) from nk").fetchall()[0][0]))
    (OUT / "memory.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    (OUT / "memory.json").chmod(0o600)
    print(f"memory: {len(oracles)} oracles · {time.time() - t0:.0f}s -> {OUT / 'memory.json'}")
    for o in oracles[:14]:
        print(f"  {o['name'][:30]:<30} prompts {o['prompts']:>6,} notes {o['notes']:>6,} recall {o['recall']:.0%} unasked {o['unasked']:.0%} learnings {o['learnings']}")


if __name__ == "__main__":
    main()
