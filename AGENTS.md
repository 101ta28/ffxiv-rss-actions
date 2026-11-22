# Repository Guidelines

## Project Structure

- `rss_parser.py` posts new entries from the Japanese Lodestone news, topics, and official blog feeds to Discord. Each feed has its own list of seen IDs in `news_state.json`, `topics_state.json`, or `atom_state.json`.
- `state_creator.py` seeds a feed’s seen IDs without sending messages. It overwrites `<feed_name>_state.json` beside the script.
- `stage_schedule_webhook.py` maintains one Discord message for the PvP rotation. It reads the message ID and last rotation from `stage_schedule_state.json` in the current working directory.
- `.github/workflows/actions.yml` runs the scripts every 20 minutes or on manual dispatch and commits changed state files. Embed icons use remote URLs.

## Local Development

Use Python 3.11 to match GitHub Actions. The scripts run directly and require no build step.

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install feedparser requests beautifulsoup4
```

Export `WEBHOOK_URL` for feed posts or `DISCORD_STAGE_WEBHOOK_URL` for stage updates. Use a test Discord webhook for local runs. Start in the repository root and set `RSS_URL` to the feed under test.

```sh
workdir=$(mktemp -d)
python rss_parser.py "$RSS_URL" "$workdir/feed_state.json"
stage_script="$PWD/stage_schedule_webhook.py"
(cd "$workdir" && python "$stage_script")
```

## Coding Style

Use four spaces for Python indentation, `snake_case` for functions and variables, and `UPPER_SNAKE_CASE` for module constants. When writing state, follow the existing JSON format with `ensure_ascii=False` and `indent=4`. The repository has no configured formatter or linter.

## Testing

There is no automated test suite or coverage threshold. For feed changes, run the parser twice against the same saved feed and temporary state file. The second run should print `No new entries to process.` For rotation changes, check that a second run within the same rotation preserves the message ID and skips the update.

## Commits and Pull Requests

Use a short subject describing the change, as in `Fix state file conflict handling`. History includes both English and Japanese subjects. In a pull request, name the affected feed or stage behavior and describe how you verified it. Keep test-generated state and webhook URLs out of the diff.
