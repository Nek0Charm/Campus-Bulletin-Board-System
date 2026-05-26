import DOMPurify from 'dompurify'

export function sanitizeHTML(html: string): string {
  return DOMPurify.sanitize(html, { ALLOWED_TAGS: [] })
}

export function sanitizeRichHTML(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'p',
      'br',
      'strong',
      'em',
      'u',
      'h2',
      'h3',
      'h4',
      'ul',
      'ol',
      'li',
      'a',
      'blockquote',
      'pre',
      'code',
      'img',
    ],
    ALLOWED_ATTR: ['href', 'src', 'alt', 'title'],
  })
}
