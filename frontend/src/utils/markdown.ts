import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'
import mk from 'markdown-it-katex'
import ins from 'markdown-it-ins'
import sub from 'markdown-it-sub'
import sup from 'markdown-it-sup'
import hljs from 'highlight.js'

const escapeHtml = (str: string): string =>
  str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

const md: MarkdownIt = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
  breaks: true,
  highlight: (str: string, lang: string): string => {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return (
          '<pre class="hljs"><code>' +
          hljs.highlight(str, { language: lang, ignoreIllegals: true }).value +
          '</code></pre>'
        )
      } catch {
        // fall through to default escaping
      }
    }
    return '<pre class="hljs"><code>' + escapeHtml(str) + '</code></pre>'
  },
}).enable('strikethrough')

md.use(mk, { throwOnError: false })
md.use(ins)
md.use(sub)
md.use(sup)

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
  'ins',
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
  'input', // markdown-it task list checkbox
  'label', // markdown-it task list label
  // KaTeX HTML
  'span',
  // KaTeX MathML
  'math',
  'semantics',
  'mrow',
  'annotation',
  'msup',
  'mi',
  'mn',
  'mo',
  'mtext',
  'mspace',
  'mstyle',
  'mpadded',
  'mphantom',
  'menclose',
  'mfenced',
  'mfrac',
  'mprescripts',
  'none',
  'msub',
  'msubsup',
  'mtable',
  'mtr',
  'mtd',
  'mlabeledtr',
  'mth',
  'mover',
  'munder',
  'munderover',
  // KaTeX SVG fallback
  'svg',
  'path',
  'line',
  'g',
  'defs',
  'use',
]

const ALLOWED_ATTR = [
  'href',
  'src',
  'alt',
  'title',
  'target',
  'rel',
  'class',
  'style',
  'aria-hidden',
  // checkbox task list
  'type',
  'checked',
  'disabled',
  // SVG / KaTeX
  'viewBox',
  'width',
  'height',
  'preserveAspectRatio',
  'xmlns',
  'overflow',
  'stroke-width',
  'stroke-linecap',
  'stroke',
  'fill',
  'd',
  'x',
  'y',
  'x1',
  'y1',
  'x2',
  'y2',
  'rx',
  'ry',
  'cx',
  'cy',
  'r',
  'transform',
  'marker-end',
  'marker-start',
  'stroke-dasharray',
  'stroke-linejoin',
  'stroke-miterlimit',
  'font-family',
  'font-size',
  'font-weight',
  'font-style',
  'text-anchor',
  'dominant-baseline',
  'id',
  'clip-path',
  'stroke-opacity',
  'fill-opacity',
  'encoding', // KaTeX MathML annotation
]

export function renderMarkdown(text: string): string {
  const html = md.render(text ?? '')
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOW_DATA_ATTR: true,
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
