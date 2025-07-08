"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import Header from "../components/Header"
import Footer from "../components/Footer"
import SearchBar from "../components/SearchBar"
import { Button } from "@/components/ui/button"
import { Library } from "lucide-react"

const getGreeting = () => {
  const hour = new Date().getHours()
  if (hour < 12) return "Good morning"
  if (hour < 18) return "Good afternoon"
  return "Good evening"
}

export default function DashboardPage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [greeting, setGreeting] = useState("")
  const [userName, setUserName] = useState("")
  const router = useRouter()

  useEffect(() => {
    setGreeting(getGreeting())

    const checkAuth = async () => {
      try {
        const response = await fetch('/api/auth/status', {
          credentials: 'include'
        })
        const authData = await response.json()

        if (!authData.authenticated) {
          router.push('/')
          return
        }

        if (authData.user?.given_name) {
          setUserName(authData.user.given_name)
        }
      } catch {
        router.push('/')
      }
    }

    checkAuth()
  }, [router])

  const executeSearch = (query: string) => {
    if (query.trim() !== "") {
      router.push(`/search?q=${encodeURIComponent(query)}`)
    }
  }

  return (
    <div className="flex flex-col min-h-screen bg-slate-50">
      <Header />
      <main className="flex-grow relative overflow-hidden flex items-center justify-center">
        {/* Background blobs - made non-interactive */}
        <div className="absolute top-1/4 -left-16 w-96 h-96 bg-blue-200 rounded-full mix-blend-multiply filter blur-2xl opacity-30 animate-blob pointer-events-none" />
        <div className="absolute top-1/2 -right-16 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-2xl opacity-30 animate-blob animation-delay-2000 pointer-events-none" />

        <div className="relative z-10">
          <section className="py-20 md:py-28">
            <div className="container text-center max-w-4xl mx-auto px-4 animate-fade-in">
              <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-gray-800">
                {greeting}, {userName}.
              </h1>
              <p className="mt-4 text-lg md:text-xl text-gray-600 max-w-2xl mx-auto">
                Contexta — Where your past context becomes future clarity.
              </p>
              <div className="mt-8 max-w-2xl mx-auto">
                <SearchBar
                  query={searchQuery}
                  onQueryChange={setSearchQuery}
                  onSearch={() => executeSearch(searchQuery)}
                />
              </div>
              <div className="mt-4">
                <Link href="/wikis">
                  <Button variant="outline" className="bg-white/50 backdrop-blur-sm">
                    Or, browse all current wikis
                    <Library className="h-4 w-4 ml-1.5" />
                  </Button>
                </Link>
              </div>
            </div>
          </section>
        </div>
      </main>
      <Footer />
    </div>
  )
}
