# jev-eval results site

The public results page for the jev-eval benchmark — methodology, experiment-by-experiment
results and takeaways, built from one real run's numbers (`src/data/results.js`). React + Vite,
no backend; deploys to GitHub Pages via `.github/workflows/deploy-site.yml` on every push to
`master` that touches `site/`.

```
npm install
npm run dev      # http://localhost:5173/jev_eval/
npm run build    # outputs to dist/
```

To refresh the numbers after a new benchmark run, regenerate `src/data/results.js` from the
new `results/<run_id>/` directory and push — the site redeploys automatically.
