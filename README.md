# GitHub AI Radar

A dependency-free scanner that searches GitHub for useful AI agents, frameworks, coding tools, RAG projects, and LLM infrastructure. It surfaces both established repositories and young projects growing quickly.

## Quick start

Python 3.10+ is required.

```bash
cd github-ai-radar
python3 -m github_ai_radar
```

If you are signed in with GitHub CLI (`gh auth login`), the scanner securely reuses that credential from your system keychain. Otherwise, set `GITHUB_TOKEN`; public-repository read access is sufficient.

Install the `ai-radar` command if you prefer:

```bash
python3 -m pip install -e .
ai-radar --limit 20
```

GitHub allows unauthenticated searches at a much lower rate, so the built-in eight-query scan is most reliable when authenticated. Responses are cached for one hour in `.radar-cache/`.

## Useful scans

```bash
# Find younger projects and generate a shareable report
python3 -m github_ai_radar --max-age-days 365 --min-stars 20 --markdown reports/rising.md

# Focus on TypeScript
python3 -m github_ai_radar --language TypeScript --limit 15

# Search only your own GitHub query
python3 -m github_ai_radar --only-custom --query 'topic:computer-use stars:>20 archived:false'

# Save machine-readable results
python3 -m github_ai_radar --json reports/results.json
```

Run `python3 -m github_ai_radar --help` for all options.

## How ranking works

The 0–100 score combines:

- adoption, using a logarithmic star score so giants do not drown out newcomers;
- momentum, estimated from lifetime stars per day;
- freshness, based on the latest repository update;
- usability signals such as a detected license, implementation language, topics, homepage, and forks.

Archived projects and resource/list repositories are penalized. A GitHub search result does not contain star-history data, so “stars/day” is a lifetime estimate rather than a recent trend. For stronger trend detection, run the scanner periodically, save JSON, and compare snapshots.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT
