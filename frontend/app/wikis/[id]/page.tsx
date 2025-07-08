import { notFound } from "next/navigation"
import Link from "next/link"
import Header from "@/app/components/Header"
import Footer from "@/app/components/Footer"
import MarkdownRenderer from "@/app/components/MarkdownRenderer"
import { mockWikis } from "@/app/lib/mock-wikis"
import type { Wiki } from "@/app/lib/mock-wikis"
import { ArrowLeft } from "lucide-react"

// This is now an async Server Component. It fetches data on the server before rendering.
export default async function WikiPage({ params }: { params: { id: string } }) {
  // --- PREVIEW-FRIENDLY DATA FETCHING ---
  // In a preview environment, params.id might not be a valid ID from our mock data.
  // To prevent a "Not Found" error during preview, we first try to find the specific wiki.
  // If it's not found, we fall back to the first wiki in the mock array as a default.
  // In a real application connected to a database, the original `notFound()` call is the correct behavior.
  let wiki: Wiki | undefined = mockWikis.find((w) => w.id === params.id)

  if (!wiki) {
    // Fallback for previewing purposes
    wiki = mockWikis[0]
  }

  // If after the fallback, there's still no wiki (e.g., mockWikis is empty), then show not found.
  if (!wiki) {
    notFound()
  }

  return (
    <div className="flex flex-col min-h-screen bg-white">
      <Header />
      <main className="flex-grow w-full container mx-auto px-4 md:px-6 py-12">
        <div className="max-w-4xl mx-auto">
          <Link href="/wikis" className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-6">
            <ArrowLeft className="h-4 w-4" />
            Back to all wikis
          </Link>
          <h1 className="text-4xl font-bold tracking-tight text-gray-900">{wiki.title}</h1>
          <p className="mt-2 text-lg text-gray-500">Last updated {wiki.lastUpdated}</p>
          <hr className="my-8" />
          <MarkdownRenderer content={wiki.content} />
        </div>
      </main>
      <Footer />
    </div>
  )
}
