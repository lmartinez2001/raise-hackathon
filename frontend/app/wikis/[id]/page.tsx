import { notFound } from "next/navigation"
import Link from "next/link"
import Header from "@/app/components/Header"
import Footer from "@/app/components/Footer"
import MarkdownRenderer from "@/app/components/MarkdownRenderer"
import { ArrowLeft } from "lucide-react"

async function getWiki(id: string) {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_FRONTEND_URL || 'http://localhost:8000'}/api/wikis/${id}`, {
      cache: 'no-store'
    })

    if (!response.ok) {
      return null
    }

    return await response.json()
  } catch (error) {
    console.error('Error fetching wiki:', error)
    return null
  }
}

export default async function WikiPage({ params }: { params: { id: string } }) {
  const resolvedParams = await params
  const wiki = await getWiki(resolvedParams.id)

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
