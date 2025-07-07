"use client"

import { useState } from "react"
import Header from "./components/Header"
import Footer from "./components/Footer"
import SearchBar from "./components/SearchBar"
import AiSummaryCard from "./components/AiSummaryCard"
import SuggestedQuestions from "./components/SuggestedQuestions"
import SourceStream from "./components/SourceStream"
import Features from "./components/Features"
import UseCases from "./components/UseCases"
import ContextaInAction from "./components/ContextaInAction"
import { mockSources } from "./lib/mock-data"

export default function Home() {
  const [isSearched, setIsSearched] = useState(false)

  const handleSearch = (query: string) => {
    if (query.trim() !== "") {
      setIsSearched(true)
    }
  }

  return (
    <div className="flex flex-col min-h-screen bg-slate-50">
      <Header />
      {!isSearched ? (
        <main className="flex-grow">
          <section className="flex items-center justify-center py-20 md:py-32 bg-gradient-to-br from-blue-100 via-white to-purple-100">
            <div className="container text-center max-w-3xl mx-auto px-4 animate-fade-in">
              <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tighter text-gray-900">
                <span className="text-blue-600">Unlock</span> the insights your
                <br />
                team loses in conversations.
              </h1>
              <p className="mt-4 md:mt-6 text-lg md:text-xl text-gray-700 max-w-2xl mx-auto">
                Contexta is your unified search across meetings, Slack, and docs. You get an answer, not buried in tabs.
              </p>
              <div className="mt-8 max-w-2xl mx-auto">
                <SearchBar onSearch={handleSearch} />
              </div>
            </div>
          </section>
          <Features />
          <UseCases />
          <ContextaInAction />
        </main>
      ) : (
        <main className="flex-grow w-full max-w-4xl mx-auto px-4 py-8">
          <div className="sticky top-[65px] z-10 bg-slate-50/80 backdrop-blur-sm -mx-4 px-4 py-2 rounded-lg">
            <SearchBar onSearch={handleSearch} />
          </div>
          <div className="mt-8 space-y-8 animate-fade-in">
            <AiSummaryCard />
            <SuggestedQuestions />
            <SourceStream sources={mockSources} />
          </div>
        </main>
      )}
      <Footer />
    </div>
  )
}
