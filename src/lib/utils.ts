import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** "European Knowledge Center" -> "EKC", for organisations without a logo. */
export function initials(name: string) {
  const words = name.replace(/<[^>]+>/g, '').split(/[\s.-]+/).filter((w) => /^[A-ZÀ-Ý]/.test(w));
  return (words.length ? words : [name]).slice(0, 3).map((w) => w[0]).join('').toUpperCase();
}

/** "Eötvös Loránd University" -> "eotvos-lorand-university", used to find content/cv/logos/<slug>.png */
export function slugify(name: string) {
  return name
    .replace(/<[^>]+>/g, '')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}
