import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Served from https://raguram-venkat.github.io/jev_eval/ (a project Pages site, not a
// user/org site), so every asset path needs the repo name as a base.
export default defineConfig({
  base: '/jev_eval/',
  plugins: [react()],
})
