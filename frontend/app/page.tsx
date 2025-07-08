"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Header from "./components/Header"
import Footer from "./components/Footer"
import Features from "./components/Features"
import UseCases from "./components/UseCases"
import ContextaInAction from "./components/ContextaInAction"
import SearchBar from "./components/SearchBar"
import AiSummaryCard from "./components/AiSummaryCard"
import SuggestedQuestions from "./components/SuggestedQuestions"
import SourceStream from "./components/SourceStream"
import { Button } from "@/components/ui/button"
import { PlayCircle, Loader2 } from "lucide-react"
import { GoogleIcon } from "./components/GoogleIcon"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
}

const initialSummary =
  'In the Q2 planning meetings, the primary data privacy concerns revolved around GDPR compliance for new European markets. The team discussed potential vulnerabilities in the user data encryption methods, as noted in the "Project Titan Security Review" document. A follow-up action was assigned to Sarah in the #security Slack channel to investigate third-party vendor compliance.'

const initialSuggestedQuestions = [
  "What actions were assigned to me?",
  "Was there any disagreement?",
  "Any related updates shared after the meeting?",
]

// Mock function to generate new suggestions based on context
const generateNewSuggestions = (lastMessage: string): string[] => {
  if (lastMessage.toLowerCase().includes("disagreement")) {
    return ["Who was involved in the disagreement?", "What was the proposed timeline?", "Summarize Alex Chen's point."]
  }
  if (lastMessage.toLowerCase().includes("actions")) {
    return ["What was Sarah's deadline?", "Is there a ticket for this action item?", "Where can I find the whitepaper?"]
  }
  return [
    "Can you elaborate on the key management system?",
    "What were the other security concerns?",
    "Who is Alex Chen?",
  ]
}

// Mock sources data
const mockSources = [
  { id: "1", title: "Project Titan Security Review", url: "https://example.com/project-titan-security-review" },
  { id: "2", title: "Q2 Planning Meetings Notes", url: "https://example.com/q2-planning-meetings-notes" },
]

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [isSearched, setIsSearched] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isSigningIn, setIsSigningIn] = useState(false)
  const router = useRouter()

  const [messages, setMessages] = useState<Message[]>([{ id: "1", role: "assistant", content: initialSummary }])
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>(initialSuggestedQuestions)
  const [followUpInputValue, setFollowUpInputValue] = useState("")
  const [isReplying, setIsReplying] = useState(false)
  const [isInputExpanded, setIsInputExpanded] = useState(false)

  const executeSearch = (query: string) => {
    if (query.trim() !== "") {
      setSearchQuery(query)
      setIsLoading(true)
      setIsSearched(false)
      // Reset chat on new search
      setMessages([{ id: "1", role: "assistant", content: initialSummary }])
      setSuggestedQuestions(initialSuggestedQuestions)
      setFollowUpInputValue("")
      setIsInputExpanded(false)
      setTimeout(() => {
        setIsLoading(false)
        setIsSearched(true)
      }, 5000)
    }
  }

  const handleSendMessage = () => {
    if (followUpInputValue.trim() === "") return

    const newUserMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: followUpInputValue,
    }
    setMessages((prev) => [...prev, newUserMessage])
    setFollowUpInputValue("")
    setIsReplying(true)

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `In response to your question "${newUserMessage.content}", the main point of disagreement was about the implementation timeline for the new encryption keys, not the necessity of the keys themselves. This was raised by Alex Chen in the 'Project Titan Security Review' document.`,
      }
      setMessages((prev) => [...prev, aiResponse])
      setSuggestedQuestions(generateNewSuggestions(newUserMessage.content))
      setIsReplying(false)
    }, 2000)
  }

  const handleSuggestedQuestionClick = (question: string) => {
    setFollowUpInputValue(question)
    setIsInputExpanded(true)
  }

  const handleScrollToDemo = () => {
    const demoSection = document.getElementById("demo")
    if (demoSection) {
      demoSection.scrollIntoView({ behavior: "smooth" })
    }
  }

  async function handleGoogleLogin() {
    try {
      // Instead of fetch, directly redirect to the backend login endpoint
      window.location.href = "/api/auth/login"
    } catch (err) {
      console.error(err)
      alert("Login failed; check console for details.")
    }
  }

  const renderMainContent = () => {
    if (isLoading) {
      return <div>Loading...</div>
    }

    if (isSearched) {
      return (
        <div className="relative overflow-hidden">
          <div className="absolute top-1/4 -left-16 w-96 h-96 bg-blue-200 rounded-full mix-blend-multiply filter blur-2xl opacity-30 animate-blob" />
          <div className="absolute top-1/2 -right-16 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-2xl opacity-30 animate-blob animation-delay-2000" />

          <div className="relative w-full max-w-4xl mx-auto px-4 py-8">
            <div className="sticky top-[65px] z-10 bg-slate-50/80 backdrop-blur-sm -mx-4 px-4 py-2 rounded-lg">
              <SearchBar
                query={searchQuery}
                onQueryChange={setSearchQuery}
                onSearch={() => executeSearch(searchQuery)}
              />
            </div>
            <div className="mt-8 space-y-6 animate-fade-in">
              <AiSummaryCard
                messages={messages}
                inputValue={followUpInputValue}
                onInputChange={setFollowUpInputValue}
                onSendMessage={handleSendMessage}
                isReplying={isReplying}
                isExpanded={isInputExpanded}
                onExpansionChange={setIsInputExpanded}
              />
              <SuggestedQuestions questions={suggestedQuestions} onQuestionClick={handleSuggestedQuestionClick} />
              <SourceStream sources={mockSources} />
            </div>
          </div>
        </div>
      )
    }

    return (
      <>
        <section className="flex items-center justify-center py-20 md:py-32 bg-gradient-to-br from-blue-100 via-white to-purple-100">
          <div className="container text-center max-w-4xl mx-auto px-4 animate-fade-in">
            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tighter text-gray-900">
              <span className="text-blue-600">Unlock</span> the insights your
              <br />
              <span className="whitespace-nowrap">team loses in conversations.</span>
            </h1>
            <p className="mt-4 md:mt-6 text-lg md:text-xl text-gray-700 max-w-2xl mx-auto">
              Stop wasting hours digging for info and manually organizing context.
              <br />A full-picture answer—pulled from meetings, Slack, and docs—so you focus on what matters.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button size="lg" onClick={handleGoogleLogin} disabled={isSigningIn}>
                {isSigningIn ? (
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                ) : (
                  <GoogleIcon className="mr-2 h-6 w-6" />
                )}
                {isSigningIn ? "Redirecting..." : "Sign In with Google"}
              </Button>
              <Button size="lg" variant="outline" onClick={handleScrollToDemo} className="bg-white/50">
                See Contexta in Action
                <PlayCircle className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </div>
        </section>
        <Features />
        <UseCases />
        <ContextaInAction />
      </>
    )
  }

  return (
    <div className="flex flex-col min-h-screen bg-slate-50">
      <Header />
      <main className="flex-grow">{renderMainContent()}</main>
      <Footer />
    </div>
  )
}
