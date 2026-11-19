# Who decides, and how that holds

RoboHub's repositories are public: anyone can read them, fork them and open a
pull request. The maintainer — one person for now, named in `MAINTAINERS.yml` —
approves requirements, accepts architecture decisions and merges to `main`. This
page is how that is made to hold, and what to do to switch it on.

## What holds it

| Layer | What it does | Where |
|---|---|---|
| **A protected `main`** | `main` cannot be deleted or force-pushed; a change arrives by pull request, approved by a code owner, with CI green. The repository's administrators bypass it, so the maintainer can still push and merge their own work. | A GitHub ruleset on every repository |
| **CODEOWNERS** | Names the maintainer as owner of everything, and in particular of `docs/requirements/`, `docs/architecture/`, every `module.yml`, `MAINTAINERS.yml` and `.github/`. With the ruleset, no pull request touching them merges without the maintainer's approval. | `.github/CODEOWNERS` in every repository |
| **`rho req check`** | In CI, on every pull request: refuses a commit that approves a requirement or accepts an ADR unless its author is in `MAINTAINERS.yml`, read as it was at the pull request's base, so a contributor cannot add themselves in the same change. | The shared workflow's *Requirements and decisions* step |
| **The pull request template** | Asks every change for the requirement it serves, its ADRs and its tests. | `.github/pull_request_template.md` |

The first two are the authority. The third is a guard: a commit's author name is
whatever the committer wrote, so it can catch a mistake but not stop someone set
on it — the protected branch and the code-owner review are what do.

## Switching it on

The ruleset is one file, `.github/rulesets/main.json` in this repository, and one
script applies it to every repository — the eighteen RoboHub repositories and
rho:

1. **A token.** On GitHub: *Settings → Developer settings → Personal access
   tokens → Fine-grained tokens → Generate new token*. Resource owner:
   `RoboHubPlatform` (and a second token, or the same steps, for `rho-language`);
   repository access: *All repositories*; permissions: **Administration: Read and
   write**. Copy it; it is shown once.
2. **See what it would do.** From a checkout of this repository:

   ```sh
   GITHUB_TOKEN=<token> tools/apply-rulesets.sh
   ```

   Each repository is listed with *would create* or *would update*. Nothing
   changes.
3. **Apply it.**

   ```sh
   GITHUB_TOKEN=<token> tools/apply-rulesets.sh --apply
   ```

   Each repository says *created* or *updated*, or why GitHub refused.
4. **Delete the token**, or let it expire: it can change every repository's
   settings.

The same can be done by hand per repository: *Settings → Rules → Rulesets → New
ruleset → Import a ruleset*, choosing `.github/rulesets/main.json` (for rho,
change the required check to `build-and-test`).

## What it means day to day

- **The maintainer** pushes to `main` directly, or merges their own pull request
  without a second approval: administrators bypass the ruleset. CI still runs on
  every push.
- **Anyone else** opens a pull request from a fork or a branch. It merges only
  when CI is green and the maintainer has approved it; a push after the approval
  asks for it again.
- **A proposed requirement or ADR** from a contributor arrives as `proposed`.
  The maintainer approves it — in the keeper's Developer section or with
  `rho req set-status` — in their own commit.

## Checking it holds

After applying, *Settings → Rules → Rulesets* on any repository shows `main`,
active, with the maintainer's role in the bypass list. A pull request from
another account shows *Review required* and *Code owner review required* until
the maintainer approves.
