# Setup: things only John can do

Local run needs nothing beyond Python 3.12 and Node 22. `make run` creates `.venv`, installs pinned dependencies, loads GitHub and INFORMANT data, checks freshness and runs `dbt build`. `make site` builds the static pages, the Evidence report under `/explore`, and `site/_headers`; `npm ci` installs wrangler and the Playwright tests (`npm run test:e2e` after `make site`; `npx playwright install chromium` once); `make deploy` deploys by hand (needs `wrangler` logged in).

## For the nightly workflow to publish the site

The workflow builds the warehouse and the site with no secrets. Publishing needs Cloudflare credentials:

```
gh secret set CLOUDFLARE_API_TOKEN --repo Noir-Cpu/noir-wiretap
gh secret set CLOUDFLARE_ACCOUNT_ID --repo Noir-Cpu/noir-wiretap
```

Create the token at dash.cloudflare.com, My Profile, API Tokens, with the "Edit Cloudflare Workers" template. Until both secrets exist, the workflow still passes and prints a warning that the deploy step was skipped.

## Optional

- Branch protection on `main` requiring the `check` and `audit` jobs, once you want Dependabot PRs gated.
- A GitHub Environment named `production` limited to the `main` branch, holding the two Cloudflare secrets instead of repository secrets, so a workflow run from any other branch cannot read them. The nightly workflow does not use an environment yet.
- Enable GitHub code scanning if it is not on (CodeQL runs, results only appear if enabled).
