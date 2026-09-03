# GitHub AI Radar

A dependency-free discovery engine for useful AI agents, infrastructure, and the creators building them. It deliberately searches beyond the GitHub front page to surface established projects, fast risers, and low-star hidden gems.

## What makes the radar different

- **23 discovery lanes:** established projects plus rising and fresh searches across agentic systems, multi-agent orchestration, coding agents, computer use, MCP, voice, memory, observability, local inference, and embodied AI.
- **Real momentum:** saves local star snapshots and measures actual gains between scans at least six hours apart.
- **Creator radar:** groups projects by owner and scores emerging builders with repeat signals across a portfolio.
- **Diverse results:** caps any one creator or category so famous frameworks cannot monopolize the report.
- **Useful-project signals:** rewards recent code pushes, licensing, language, topics, forks, and a usable project description; penalizes archives, forks, and list/tutorial repositories.
- **Honest labels:** distinguishes observed star velocity from the lifetime estimate used before enough history exists.

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

GitHub allows unauthenticated searches at a much lower rate, so the broad scan is designed for authenticated use. Responses are cached for one hour in `.radar-cache/`; star history is stored locally in `.radar-history.json`. Neither file is committed.

## Useful scans

```bash
# Focus entirely on emerging projects and creators
python3 -m github_ai_radar --mode emerging

# Generate a shareable emerging-tech report
python3 -m github_ai_radar --mode emerging --markdown reports/rising.md

# Use 15 searches instead of 23 when you need a faster scan
python3 -m github_ai_radar --quick

# Focus on TypeScript
python3 -m github_ai_radar --language TypeScript --limit 15

# Search only your own GitHub query
python3 -m github_ai_radar --only-custom --query 'topic:computer-use stars:>20 archived:false'

# Save machine-readable results
python3 -m github_ai_radar --json reports/results.json
```

Run `python3 -m github_ai_radar --help` for all options.

## How ranking works

The 0–100 project score combines:

- adoption, using a logarithmic star score so giants do not drown out newcomers;
- momentum, measured from saved snapshots when possible and otherwise estimated from project age;
- freshness, based on the latest code push;
- usability signals such as a detected license, implementation language, topics, homepage, and forks.
- novelty, giving young projects a controlled lift without allowing novelty alone to win.

Archived projects, forks, and resource/list repositories are penalized. Results are split into `breakout`, `hidden gem`, `rising`, `established`, and `candidate` signals. Creator scores combine the strongest project, portfolio breadth, reach, and number of emerging signals.

The first run creates the baseline. Run it again six hours or more later to activate observed momentum automatically. Use `--no-history` for a stateless scan or `--history some-file.json` to keep separate watchlists.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT
