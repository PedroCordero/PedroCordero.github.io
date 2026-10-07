import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

// One folder per project in content/projects/: index.md plus its images.
// The fields below are checked on every build; see content/projects/_template.md.
const projects = defineCollection({
  loader: glob({
    pattern: '*/index.md',
    base: './content/projects',
    generateId: ({ entry }) => entry.replace(/\/index\.md$/, ''),
  }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      summary: z.string(),
      date: z.coerce.date(),
      cover: image().optional(),
      tags: z.array(z.string()).default([]),
      links: z.array(z.object({ label: z.string(), url: z.string().url() })).default([]),
      featured: z.boolean().default(false),
      draft: z.boolean().default(false),
    }),
});

// Free-form pages in content/pages/. home.md is the home page intro;
// every other file becomes its own page, linked in the menu.
const pages = defineCollection({
  loader: glob({ pattern: '*.md', base: './content/pages' }),
  schema: z.object({
    title: z.string(),
    description: z.string().optional(),
    order: z.number().default(100),
  }),
});

export const collections = { projects, pages };
