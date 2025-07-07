"use client"

import type React from "react"

import { useState } from "react"
import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

interface SearchBarProps {
  onSearch: (query: string) => void
}

export default function SearchBar({ onSearch }: SearchBarProps) {
  const [query, setQuery] = useState("What were the concerns around data privacy in our Q2 planning meetings?")

  const handleSearch = () => {
    onSearch(query)
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSearch()
    }
  }

  return (
    <div className="relative">
      <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
      <Input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyPress}
        placeholder="Ask a question about your meetings, docs, and chats..."
        className="w-full pl-11 pr-24 h-14 rounded-lg shadow-md text-base"
      />
      <Button onClick={handleSearch} className="absolute right-2.5 top-1/2 -translate-y-1/2 h-10 px-5">
        Search
      </Button>
    </div>
  )
}
