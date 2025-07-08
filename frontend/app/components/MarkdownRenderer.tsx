"use client"

// --- PRODUCTION-READY MARKDOWN RENDERING ---
// This component is responsible for taking a raw Markdown string and converting
// it into properly formatted HTML. It uses the `react-markdown` and `remark-gfm`
// libraries, which support standard Markdown as well as GitHub Flavored Markdown (tables, etc.).
//
// To use it, simply pass the Markdown content from your database to the `content` prop.
// No changes are needed here for production.

import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

interface MarkdownRendererProps {
  content: string
}

export default function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <div className="prose prose-slate max-w-none lg:prose-lg">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  )
}
