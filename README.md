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

Git LFS (Large File Support)
----------------------------
This repo stores several media assets (videos and high-resolution images) in the `assets/` folder. To keep the Git repository small and handle large binary files efficiently, the project includes a `.gitattributes` file configured to use Git LFS for common media types.

Local setup steps (run these once on your machine):

```bash
# install Git LFS (macOS / Linux / Windows)
git lfs install

# if you want to re-track files locally (already configured in .gitattributes):
git lfs track "assets/*.mp4" "assets/*.mov" "assets/*.jpg" "assets/*.png"

# add the attributes and stage media
git add .gitattributes
git add assets/*
git commit -m "Add Git LFS tracking for media assets"
git push
```

Notes:
- If the remote repository already contains large files committed before enabling LFS, consider using `git lfs migrate import --include="assets/*"` to migrate existing assets into LFS (this rewrites history; use with caution).
- Installing Git LFS is required only once per machine/user (and run `git lfs install`).
