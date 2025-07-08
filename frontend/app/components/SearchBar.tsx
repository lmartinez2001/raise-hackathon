"use client"

import type React from "react"
import { Search, Sparkles } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"

interface SearchBarProps {
  query: string
  onQueryChange: (query: string) => void
  onSearch: () => void
}

export default function SearchBar({ query, onQueryChange, onSearch }: SearchBarProps) {
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      onSearch()
    }
  }

  return (
    <div className="relative">
      <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
      <Input
        type="text"
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        onKeyDown={handleKeyPress}
        placeholder=""
        className="w-full pl-11 pr-32 h-14 rounded-lg shadow-md text-base"
      />
      <Button
        onClick={onSearch}
        className="absolute right-2.5 top-1/2 -translate-y-1/2 h-10 px-5 flex items-center gap-2"
      >
        <Sparkles className="h-4 w-4" />
        Search
      </Button>
    </div>
  )
}
