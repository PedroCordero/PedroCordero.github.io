// @ts-check
import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://pedrocordero.hu',
  redirects: {
    // The old site (pedrocordero.github.io/portfolio) is printed on CVs already sent.
    '/portfolio': '/',
  },
});
