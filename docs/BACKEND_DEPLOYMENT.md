# FRIP Beta Backend Deployment

This GitHub Pages beta frontend is static. It still needs a deployed FastAPI backend for the real work.

## What The Beta Frontend Already Expects

Set these values in `docs/index.html` inside `window.FRIP_BETA_CONFIG` before publishing:

```html
window.FRIP_BETA_CONFIG = {
  apiBaseUrl: "https://your-backend-domain.com",
  clerkPublishableKey: "pk_...",
  clerkJsVersion: "5.56.0",
  supabaseUrl: "https://your-project.supabase.co",
  supabaseAnonKey: "ey...",
  betaSignalTable: "beta_interest_signals",
  appName: "Frontier Research Intelligence Beta"
};
```

## Backend Requirements

You need a public backend URL with HTTPS.

Recommended hosts:

- Render
- Railway
- Fly.io
- a VPS later if you want more control

The backend must expose:

- `/research/search`
- `/research/arxiv-search`
- `/research/arxiv-ingest`
- `/research/federated-search`
- `/research/paper/{work_id}`
- `/research/compare-papers`
- `/documents/ask`
- `/product/citations`
- `/product/auth/sync-profile`
- `/product/workspace/{user_id}`
- `/product/workspace/{user_id}/save-paper`
- `/product/workspace/{user_id}/queue-paper`
- `/product/workspace/{user_id}/favorite-paper`
- `/product/uploads/{user_id}`
- `/product/uploads/local`
- `/product/uploads/url`

## Required Backend Environment Variables

Auth:

- `CLERK_PUBLISHABLE_KEY`
- `CLERK_SECRET_KEY` or `CLERK_JWKS_JSON` or `CLERK_JWT_PUBLIC_KEY`
- `CLERK_JWT_ISSUER`
- `CLERK_JWT_AUDIENCES`

Supabase:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY` if your backend uses service-level writes

Stripe:

- `STRIPE_PUBLISHABLE_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ID_STUDENT`
- `STRIPE_PRICE_ID_PRO`
- `STRIPE_PRICE_ID_ENTERPRISE`

App:

- `APP_BASE_URL=https://your-backend-domain.com`

## CORS

GitHub Pages is a different origin than your backend.

Your FastAPI deployment must allow requests from:

- `https://<your-github-username>.github.io`
- and, if using a project site:
- `https://<your-github-username>.github.io/<repo-name>`

Recommended FastAPI middleware pattern:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourusername.github.io",
        "https://yourusername.github.io/frontier-research-intelligence-platform",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## GitHub Pages Setup

1. Push this repo to GitHub.
2. Go to repo `Settings -> Pages`.
3. Set source to:
   - `Deploy from a branch`
   - branch: `main`
   - folder: `/docs`
4. Save.
5. GitHub Pages will publish `docs/index.html`.

If this is a project site, the public URL will look like:

`https://yourusername.github.io/frontier-research-intelligence-platform/`

## Beta Signal Capture

The beta page can save recommendation willingness directly to Supabase using:

- `supabaseUrl`
- `supabaseAnonKey`
- table: `beta_interest_signals`

Before that works, apply:

- [poc_beta_interest_schema.sql](/Users/6ixbio/Downloads/frontier-research-intelligence-platform/supabase/poc_beta_interest_schema.sql)

## Clerk Setup For GitHub Pages

In Clerk:

1. Add your GitHub Pages URL as an allowed redirect/origin.
2. Add the backend domain as a JWT authorized party if needed.
3. Add the production GitHub Pages URL once it exists.
4. Keep localhost and preview URLs during testing.

## What Still Needs A Real Backend Host

GitHub Pages cannot run:

- FastAPI
- uploads parsing
- background jobs
- webhook handlers
- Stripe server-side checkout session creation
- Clerk server-side JWT verification

That is why this beta page is static, but not backend-free.

## Recommended Proof-Of-Concept Hosting Stack

- GitHub Pages for the beta frontend
- Render or Railway for FastAPI
- Supabase for persistent user and beta data
- Clerk for auth
- Stripe for later monetization

## Launch Sequence

1. Deploy the FastAPI backend.
2. Apply Supabase schema updates.
3. Set backend env vars.
4. Enable CORS for your GitHub Pages origin.
5. Add Clerk publishable key and Supabase anon key to `docs/index.html`.
6. Publish `/docs` on GitHub Pages.
7. Test:
   - sign in
   - profile sync
   - beta signal save
   - search
   - open paper
   - ask paper
   - save paper
   - uploads

## Honest Constraint

This beta page is intentionally lighter than the main app, but it still depends on the backend for the real product behavior.
