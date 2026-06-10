import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

export async function GET(context: APIContext) {
  const entries = await getCollection('entries');
  return rss({
    title: 'RE-Library',
    description:
      'A context7-style knowledge base for Reverse Engineering — techniques, anti-analysis bypass, Android/iOS, and more.',
    site: context.site ?? 'https://heretek-ai.github.io/RE-Library',
    items: entries
      .sort((a, b) => (a.data.updated < b.data.updated ? 1 : -1))
      .map((entry) => {
        const slug = entry.id.replace(/\.md$/, '');
        return {
          title: entry.data.title,
          pubDate: new Date(entry.data.updated),
          description: entry.data.summary,
          link: `/categories/${entry.data.category}/#${slug}`,
          categories: [
            entry.data.category,
            ...entry.data.tags,
            ...entry.data.platforms,
          ],
        };
      }),
    customData: '<language>en-us</language>',
  });
}
