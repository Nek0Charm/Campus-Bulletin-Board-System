/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

declare module 'markdown-it-katex' {
  import type MarkdownIt from 'markdown-it'
  function plugin(md: MarkdownIt, options?: Record<string, unknown>): void
  export = plugin
}

declare module 'markdown-it-ins' {
  import type MarkdownIt from 'markdown-it'
  function plugin(md: MarkdownIt): void
  export default plugin
}

declare module 'markdown-it-sub' {
  import type MarkdownIt from 'markdown-it'
  function plugin(md: MarkdownIt): void
  export = plugin
}

declare module 'markdown-it-sup' {
  import type MarkdownIt from 'markdown-it'
  function plugin(md: MarkdownIt): void
  export = plugin
}
