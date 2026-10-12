// @ts-check
import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  site: 'https://pedrocordero.hu',
  integrations: [react()],
  vite: {
    plugins: [tailwindcss()],
  },
  redirects: {
    // The old site (pedrocordero.github.io/portfolio) is printed on CVs already sent.
    '/portfolio': '/',
  },
});
