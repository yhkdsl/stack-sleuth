# Demo Assets

These assets are safe portfolio visuals derived from the checked-in sample trace
and documented CLI output. Dashboard PNG/GIF assets are captured from the real
React `/replay` route. Terminal visuals remain synthetic so local shell history
and account details never enter the repository.

| Asset | Use |
| --- | --- |
| `terminal-demo.svg` | README terminal demo frame for `ops-agent ask` |
| `dashboard-replay-demo.gif` | Actual React replay dashboard GIF |
| `dashboard-replay-actual.png` | Actual React replay dashboard screenshot |
| `dashboard-replay.svg` | Synthetic dashboard replay frame |
| `guardrail-rejection.svg` | Guardrail rejection example for `SQL_WRITE_BLOCKED` |
| `architecture.svg` | Architecture diagram for repository docs |

The checked-in assets must not include `.env` contents, API keys, database
passwords, access tokens, real emails, phone numbers, private logs, terminal
history, unrelated applications, or local account details.

Regenerate the actual dashboard assets with `ffmpeg` available on `PATH`:

```bash
cd web-dashboard
npm ci
node scripts/capture-demo-assets.mjs
```

The script builds the dashboard, opens `/replay`, writes
`docs/assets/dashboard-replay-actual.png`, records a short temporary WebM, and
converts it to `docs/assets/dashboard-replay-demo.gif` with `ffmpeg`.

For external publication, record any live terminal video only after running the
checklist in `docs/DEMO_SCRIPT.md` and `docs/SUBMISSION_CHECKLIST.md`.
