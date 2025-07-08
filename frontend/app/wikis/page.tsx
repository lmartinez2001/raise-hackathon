"use client"

import { useState, useEffect, useCallback } from "react"
import Header from "../components/Header"
import Footer from "../components/Footer"
import WikiCard from "../components/WikiCard"
import { Input } from "@/components/ui/input"
import { Search, Loader2 } from "lucide-react"

interface Wiki {
  id: string
  title: string
  summary: string
  href: string
}

const useDebounce = (value: string, delay: number) => {
  const [debouncedValue, setDebouncedValue] = useState(value)
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)
    return () => {
      clearTimeout(handler)
    }
  }, [value, delay])
  return debouncedValue
}

export default function WikisPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [wikis, setWikis] = useState<Wiki[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const debouncedSearchTerm = useDebounce(searchTerm, 300)

  const fetchWikis = useCallback(async (query: string) => {
    setIsLoading(true)
    try {
      const response = await fetch(`/api/wikis?q=${encodeURIComponent(query)}`)
      const data = await response.json()
      setWikis(data)
    } catch (error) {
      console.error("Failed to fetch wikis:", error)
      setWikis([]) // Clear wikis on error
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchWikis(debouncedSearchTerm)
  }, [debouncedSearchTerm, fetchWikis])

  return (
    <div className="flex flex-col min-h-screen bg-slate-50">
      <Header />
      <main className="flex-grow w-full">
        <div className="bg-white border-b">
          <div className="container mx-auto px-4 md:px-6 py-8">
            <h1 className="text-4xl font-bold tracking-tight text-gray-900">Team's wiki</h1>
            <p className="mt-2 text-lg text-gray-600">Browse wikis that auto-update as your team’s knowledge grows.</p>
            <div className="mt-6 relative max-w-lg">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
              <Input
                type="text"
                placeholder="Search wikis by keyword, title, or content..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 h-12 text-base"
              />
            </div>
          </div>
        </div>
        <div className="container mx-auto px-4 md:px-6 py-12">
          {isLoading ? (
            <div className="flex justify-center items-center py-20">
              <Loader2 className="h-8 w-8 animate-spin text-gray-500" />
            </div>
          ) : wikis.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {wikis.map((wiki) => (
                <WikiCard key={wiki.id} wiki={wiki} />
              ))}
            </div>
          ) : (
            <div className="text-center py-20">
              <h3 className="text-xl font-semibold">No wikis found</h3>
              <p className="text-gray-500 mt-2">
                Try adjusting your search term or browse all wikis by clearing the search bar.
              </p>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  )
}
