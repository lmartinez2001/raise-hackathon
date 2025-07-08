"use client"

import { useState, useEffect, useCallback } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import SearchBar from "../components/SearchBar"
import AiSummaryCard from "../components/AiSummaryCard"
import SuggestedQuestions from "../components/SuggestedQuestions"
import SourceStream from "../components/SourceStream"
import SearchLoading from "../components/SearchLoading"
import type { Source } from "../lib/mock-data"

interface SourceReference {
  id: string
  type: "meeting" | "document" | "slack" | "wiki"
  title: string
}

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  sources?: SourceReference[]
}

export default function SearchResultsClient() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const initialQuery = searchParams.get("q") || ""

  const [searchQuery, setSearchQuery] = useState(initialQuery)
  const [isLoading, setIsLoading] = useState(true)

  const [messages, setMessages] = useState<Message[]>([])
  const [sources, setSources] = useState<Source[]>([])
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>([])
  const [followUpInputValue, setFollowUpInputValue] = useState("")
  const [isInputExpanded, setIsInputExpanded] = useState(false)

  const fetchSearchResults = useCallback(async (query: string) => {
    if (!query) {
      setIsLoading(false)
      return
    }
    setIsLoading(true)
    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`)
      const data = await response.json()
      setMessages(data.messages || [])
      setSources(data.sources || [])
      setSuggestedQuestions(data.suggestedQuestions || [])
    } catch (error) {
      console.error("Failed to fetch search results:", error)
      // Handle error state in UI
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSearchResults(initialQuery)
  }, [initialQuery, fetchSearchResults])

  const executeSearch = (query: string) => {
    if (query.trim() !== "" && query !== initialQuery) {
      router.push(`/search?q=${encodeURIComponent(query)}`)
    }
  }

  const handleSuggestedQuestionClick = (question: string) => {
    // When a suggested question is clicked, it should also trigger a new search
    executeSearch(question)
  }

  if (isLoading) {
    return <SearchLoading />
  }

  if (!initialQuery || messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-center text-gray-500 p-8">
        <div>
          <h2 className="text-xl font-semibold">No results found.</h2>
          <p className="mt-2">Please try another search from the dashboard.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative overflow-hidden">
      <div className="absolute top-1/4 -left-16 w-96 h-96 bg-blue-200 rounded-full mix-blend-multiply filter blur-2xl opacity-30 animate-blob" />
      <div className="absolute top-1/2 -right-16 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-2xl opacity-30 animate-blob animation-delay-2000" />

      <div className="relative w-full max-w-4xl mx-auto px-4 py-8">
        <div
          id="sticky-search-bar"
          className="sticky top-[65px] z-10 bg-slate-50/80 backdrop-blur-sm -mx-4 px-4 py-2 rounded-lg"
        >
          <SearchBar query={searchQuery} onQueryChange={setSearchQuery} onSearch={() => executeSearch(searchQuery)} />
        </div>
        <div className="mt-8 space-y-6 animate-fade-in">
          <AiSummaryCard
            messages={messages}
            inputValue={followUpInputValue}
            onInputChange={setFollowUpInputValue}
            onSendMessage={() => executeSearch(followUpInputValue)}
            isExpanded={isInputExpanded}
            onExpansionChange={setIsInputExpanded}
          />
          <SuggestedQuestions questions={suggestedQuestions} onQuestionClick={handleSuggestedQuestionClick} />
          <SourceStream sources={sources} />
        </div>
      </div>
    </div>
  )
}
