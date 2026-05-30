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
})

describe('stripMarkdown', () => {
  it('returns plain text from markdown', () => {
    const text = stripMarkdown('# Hello\n**bold** text')
    expect(text).not.toContain('<h1>')
    expect(text).not.toContain('<strong>')
    expect(text).toContain('Hello')
    expect(text).toContain('bold')
  })

  it('handles empty string', () => {
    expect(stripMarkdown('')).toBe('')
  })
})
