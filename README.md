# Personal-Website-Portfolio

## Deploy to Vercel

Quick steps to host this portfolio on Vercel:

- Option A (recommended): Import this repository in the Vercel dashboard and set the Project Root to `BALAGSO-AJ-Personal HTML web page` (or leave root `/` since `index.html` redirects to the portfolio page). Deploy.
- Option B (Vercel CLI): Install `vercel` and run:

```bash
npm i -g vercel
vercel login
vercel --prod
```

Notes:
- We added `index.html` at the repo root that redirects to the portfolio file and a `vercel.json` rewrite so the site is served at the root URL.
