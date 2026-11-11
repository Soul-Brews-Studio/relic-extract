# `.herdr/team.yaml` — a herdr team charter that lives in the repo

A herdr **session id equals a team charter repo of the same name**, and the team's
shape is a committed file in that repo (`.herdr/team.yaml`) instead of throwaway
machine-local state under `~/.local/state/herdr-room/`.

## Why

Today a room is saved per machine at
`~/.local/state/herdr-room/<session>__<room>.json`. That file is local, unversioned,
and dies with the machine. The member list, the layout, and who runs the room all
live outside git, so another machine cannot rebuild the same team and the roster has
no history.

Moving the charter into the repo fixes all three:

- **Reproducible** — any machine with the repo checked out can rebuild the exact team.
- **Versioned** — roster and layout changes show up in `git log`, reviewed like code.
- **Self-describing** — the team ships next to `CLAUDE.md`, so the repo that names the
  session also carries the session's definition.

## The mapping

```
herdr session id   =   charter repo name   =   folder holding .herdr/team.yaml
      relic5        Soul-Brews-Studio/relic5    …/Soul-Brews-Studio/relic5/.herdr/team.yaml
```

The charter repo holds the **full roster**. A member repo need carry nothing; it is
pointed at by the charter. (A member may keep a one-line `.herdr/member.yaml` naming
its team if we later want reverse lookup, but that is optional and not required by
this spec.)

## Schema

```yaml
# .herdr/team.yaml
session: relic5          # the herdr session id; MUST equal this repo's name
layout: fib              # fib | cols | rows | main
desk: relic5             # which member runs `herdr-room in/out` (the room owner)
members:
  - name: relic5         # herdr agent name
    repo: Soul-Brews-Studio/relic5
    role: hub            # free text: what this member is in the team
  - name: relic-extract
    repo: Soul-Brews-Studio/relic-extract
    role: extract        # step 2 of the chain
  - name: relic4-scan
    repo: Soul-Brews-Studio/relic4-scan
    role: scan           # step 1 of the chain
```

### Fields

| field | meaning |
|---|---|
| `session` | herdr session id. Invariant: equals the charter repo's own name. |
| `layout` | room layout passed to `herdr-room in … --layout <x>`. |
| `desk` | the single member that runs the room in/out (only the desk does). |
| `members[].name` | the herdr agent name to address the body by. |
| `members[].repo` | `<org>/<repo>` the member's body is checked out from. |
| `members[].role` | human note — what the member does in this team. |

### Deliberately NOT stored

**Pane ids** (`w1X:p2`, …). They change on every room move and are machine-and-moment
specific. The tool resolves a member to its live pane at `in` time by matching
`members[].repo` / cwd against a fresh `herdr agent list`, exactly as the room skill
already addresses bodies by cwd and name rather than by pane id.

**`saved` timestamp.** Git already records when the file changed.

## Rollout

1. Each charter repo's **own agent** commits its `.herdr/team.yaml` (per the fleet rule:
   change a repo through the agent that lives there, not from outside).
2. `herdr-room` learns to read `.herdr/team.yaml` from the charter repo: `in` builds the
   room from `members`, `out` sends them back, and the file — not
   `~/.local/state/herdr-room/…` — is the source of truth. Local state becomes a cache.
3. Migration: for each existing `<session>__<room>.json`, drop the `pane` ids, rename
   `path` → `repo` (as `<org>/<repo>`), and write the result to the charter repo's
   `.herdr/team.yaml`.

## Example in this repo

`.herdr/team.example-relic5.yaml` is the relic5 team written in this schema, for
reference. The real file belongs in `Soul-Brews-Studio/relic5/.herdr/team.yaml`,
landed there by relic5's own agent.
