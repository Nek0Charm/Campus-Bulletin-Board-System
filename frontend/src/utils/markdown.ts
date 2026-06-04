import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  breaks: true,
}).enable('strikethrough')

const defaultLinkRender =
  md.renderer.rules.link_open ??
  ((tokens, idx, options, _env, self) => self.renderToken(tokens, idx, options))

md.renderer.rules.link_open = (tokens, idx, options, _env, self) => {
  const token = tokens[idx]
  if (!token) return defaultLinkRender(tokens, idx, options, _env, self)
  token.attrSet('target', '_blank')
  token.attrSet('rel', 'noopener noreferrer')
  return defaultLinkRender(tokens, idx, options, _env, self)
}

const ALLOWED_TAGS = [
  'p',
  'br',
  'hr',
  'strong',
  'em',
  'u',
  'del',
  's',
  'sup',
  'sub',
  'h1',
  'h2',
  'h3',
  'h4',
  'h5',
  'h6',
  'ul',
  'ol',
  'li',
  'a',
  'blockquote',
  'pre',
  'code',
  'img',
  'table',
  'thead',
  'tbody',
  'tr',
  'th',
  'td',
]

const ALLOWED_ATTR = ['href', 'src', 'alt', 'title', 'target', 'rel', 'class']

export function renderMarkdown(text: string): string {
  const html = md.render(text ?? '')
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
  })
}

export function stripMarkdown(text: string): string {
  if (!text) return ''
  const html = md.render(text)
  const stripped = DOMPurify.sanitize(html, { ALLOWED_TAGS: [] })
  const textarea = document.createElement('textarea')
  textarea.innerHTML = stripped
  return textarea.value
}
