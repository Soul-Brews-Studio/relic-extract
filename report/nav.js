// Warp points: a column of dots on the right, one per section, part and month; hover names it, the current one is
// lit, a click glides there. Keys: ] next, [ previous, t top. Also builds the overview and the data card.
/* global h, main, t, FINDINGS, tiles */

{
  // the data, last
  const dc = h("section", "card", null, main);
  dc.id = "s-data";
  h("h2", null, t("data.h"), dc);
  h("p", "lead", t("data.lead"), dc);
  h("pre", null, "duckdb -c \"select * from 'monthly.parquet' where metric = 'tiers' order by month\"", dc).tabIndex = 0;

  // the overview: every section's finding in one line, right after the tiles
  const ov = h("section", "card", null, null);
  ov.id = "s-overview";
  main.insertBefore(ov, tiles.nextSibling);
  h("h2", null, t("overview.h"), ov);
  h("p", "lead", t("overview.lead"), ov);
  const ul = h("ol", "findings", null, ov);
  FINDINGS.filter((f) => f.lead).forEach((f) => {
    const li = h("li", null, null, ul);
    const a = h("a", null, f.title, li);
    a.href = "#" + f.id;
    h("span", null, " — " + f.lead, li);
  });

  const cards = [...main.querySelectorAll("section.card, div.part")];
  cards.forEach((c, i) => { if (!c.id) c.id = "s-" + i; });

  // a column of dots on the right edge: parts are rings, sections dots, months small dots; the label shows on hover
  // and focus; the current one is lit; a click glides there
  const rail = h("nav", "dots", null, document.body);
  rail.setAttribute("aria-label", t("warp"));
  const items = cards.map((c) => {
    const kind = c.classList.contains("month") ? "m" : c.classList.contains("part") ? "p" : "s";
    const label = kind === "p" ? c.textContent : (c.querySelector("h2")?.textContent || c.id);
    const a = h("a", "wp wp-" + kind, null, rail);
    a.href = "#" + c.id;
    a.setAttribute("aria-label", label);
    h("span", "wp-l", label, a);
    a.addEventListener("click", (e) => {
      e.preventDefault();
      c.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
      history.replaceState(null, "", "#" + c.id);
      c.classList.remove("arrive");
      void c.offsetWidth;
      c.classList.add("arrive");
    });
    return [c, a];
  });

  let cur = -1;
  const light = () => {
    const y = innerHeight * 0.3;
    let k = 0;
    cards.forEach((c, i) => { if (c.getBoundingClientRect().top < y) k = i; });
    if (k === cur) return;
    if (cur >= 0) items[cur][1].removeAttribute("aria-current");
    items[k][1].setAttribute("aria-current", "true");
    cur = k;
  };
  let raf = 0;
  addEventListener("scroll", () => { if (!raf) raf = requestAnimationFrame(() => { raf = 0; light(); }); }, { passive: true });
  light();
  addEventListener("keydown", (e) => {
    if (e.target.closest("input, textarea, summary") || e.metaKey || e.ctrlKey || e.altKey) return;
    const go = (i) => items[Math.max(0, Math.min(items.length - 1, i))][1].click();
    if (e.key === "]") go(cur + 1);
    else if (e.key === "[") go(cur - 1);
    else if (e.key === "t") scrollTo({ top: 0, behavior: "smooth" });
  });
  if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView();
}
