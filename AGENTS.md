# Project working conventions

- Commit and push at significant, tested checkpoints for recoverability, as
  requested by the user. Inspect the staged changes and check for credentials
  and generated bulk before committing. Report the commit and whether the push
  was verified. Do not force-push or discard unrelated work.
- Keep source, tests, dependency locks, research notes and compact result evidence
  under version control. Keep environments, downloaded datasets/upstream repos,
  credentials, generated media and large binary artifacts out of Git. Preserve
  source URLs, versions and hashes needed to reconstruct excluded inputs.
- Follow `research/milestones.md` and its standing welfare constraint for neural
  protocols. Mechanical/offline tests are not neural welfare assessments. Do not
  equate a quiet guard with absence of suffering or anatomy with validated dynamics.
