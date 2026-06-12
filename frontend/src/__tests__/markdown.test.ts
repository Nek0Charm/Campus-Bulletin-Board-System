import { describe, it, expect } from 'vitest'
import { renderMarkdown, stripMarkdown } from '@/utils/markdown'

describe('renderMarkdown', () => {
  it('renders plain text', () => {
    expect(renderMarkdown('Hello')).toContain('<p>Hello</p>')
  })

  it('renders bold text', () => {
    expect(renderMarkdown('**bold**')).toContain('<strong>bold</strong>')
  })

  it('renders links with target=_blank', () => {
    const html = renderMarkdown('[click](https://example.com)')
    expect(html).toContain('target="_blank"')
    expect(html).toContain('rel="noopener noreferrer"')
  })

  it('strips malicious HTML', () => {
    const html = renderMarkdown('<script>alert("xss")</script>')
    // markdown-it with html:false escapes raw tags
    expect(html).not.toContain('<script>')
    expect(html).toContain('&lt;script&gt;')
  })

  it('escapes raw HTML as safe text', () => {
    const html = renderMarkdown('<img src=x onerror="alert(1)">')
    // markdown-it with html:false escapes raw HTML, DOMPurify passes safe text through
    expect(html).toContain('&lt;img')
  })

  it('renders Chinese text', () => {
    const html = renderMarkdown('你好，世界')
    expect(html).toContain('你好，世界')
  })

  it('converts line breaks', () => {
    const html = renderMarkdown('line1\nline2')
    expect(html).toContain('<br>')
  })

  it('handles empty string', () => {
    expect(renderMarkdown('')).toBe('')
  })

  it('renders strikethrough', () => {
    const html = renderMarkdown('~~deleted~~')
    expect(html).toContain('<s>deleted</s>')
  })

  it('preserves language class on code blocks', () => {
    const html = renderMarkdown('```python\nprint("hi")\n```')
    expect(html).toContain('class="hljs"')
    expect(html).toContain('<span')
  })

  it('renders underline with ++text++', () => {
    const html = renderMarkdown('++underlined++')
    expect(html).toContain('<ins>underlined</ins>')
  })

  it('renders subscript with ~text~', () => {
    const html = renderMarkdown('H~2~O')
    expect(html).toContain('<sub>2</sub>')
  })

  it('renders superscript with ^text^', () => {
    const html = renderMarkdown('x^2^')
    expect(html).toContain('<sup>2</sup>')
  })

  it('renders inline math with katex', () => {
    const html = renderMarkdown('inline: $x^2$')
    expect(html).toContain('katex')
    expect(html).toContain('x')
    expect(html).toContain('2')
  })

  it('renders block math with katex', () => {
    const html = renderMarkdown('$$\\sum_{i=1}^{n} i$$')
    expect(html).toContain('katex')
    expect(html).toContain('katex-display')
  })

  it('renders code block with syntax highlighting', () => {
    const html = renderMarkdown('```python\nprint("hello")\n```')
    expect(html).toContain('class="hljs"')
    expect(html).toContain('<span')
  })

  it('renders code block without language', () => {
    const html = renderMarkdown('```\nplain code\n```')
    expect(html).toContain('class="hljs"')
    expect(html).toContain('plain code')
  })

  it('preserves kaTeX data attributes', () => {
    const html = renderMarkdown('$x^2$')
    // Should contain katex classes (not stripped by DOMPurify)
    expect(html).toContain('katex')
  })
})

describe('stripMarkdown', () => {
  it('returns plain text from markdown', () => {
    const text = stripMarkdown('# Hello\n**bold** text')
    expect(text).not.toContain('<h1>')
    expect(text).not.toContain('<strong>')
    expect(text).toContain('Hello')
    expect(text).toContain('bold')
  })

  it('decodes HTML entities to plain characters', () => {
    const text = stripMarkdown('Tom & Jerry')
    expect(text).toContain('Tom & Jerry')
    expect(text).not.toContain('&amp;')
  })

  it('handles empty string', () => {
    expect(stripMarkdown('')).toBe('')
  })
})
