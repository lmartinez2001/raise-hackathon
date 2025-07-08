"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Logo } from "./Logo"
import { FileText, MessageSquare, Video } from "lucide-react"

const loadingMessages = [
  "Scanning sources...",
  "Finding connections...",
  "Analyzing documents...",
  "Synthesizing insights...",
  "Connecting to conversations...",
]

const OrbitingIcon = ({
  icon: Icon,
  className,
  style,
}: {
  icon: React.ElementType
  className?: string
  style?: React.CSSProperties
}) => (
  <div
    className={`absolute h-10 w-10 flex items-center justify-center rounded-full bg-white shadow-md border ${className}`}
    style={style}
  >
    <Icon className="h-5 w-5 text-gray-600" />
  </div>
)

export default function SearchLoading() {
  const [messageIndex, setMessageIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prevIndex) => (prevIndex + 1) % loadingMessages.length)
    }, 2000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex flex-col items-center justify-center text-center py-20 md:py-32 animate-fade-in">
      <div className="relative flex items-center justify-center h-40 w-40">
        {/* Central Logo with Pulse */}
        <div className="relative flex items-center justify-center h-24 w-24">
          <div className="absolute h-24 w-24 bg-gradient-to-br from-blue-300 to-purple-400 rounded-full blur-2xl opacity-50 animate-pulse" />
          <Logo className="h-16 w-16 text-slate-700" />
        </div>

        {/* Orbiting Icons */}
        <OrbitingIcon icon={FileText} className="animate-orbit" style={{ animationDuration: "5s" }} />
        <OrbitingIcon
          icon={MessageSquare}
          className="animate-orbit"
          style={{ animationDuration: "5s", animationDelay: "-2.5s" }}
        />
        <OrbitingIcon
          icon={Video}
          className="animate-orbit"
          style={{
            animationDuration: "5s",
            animationDelay: "-1.25s",
            transform: "rotate(120deg) translateX(60px) rotate(-120deg)",
          }}
        />
      </div>
      <p key={messageIndex} className="mt-8 text-lg text-gray-600 animate-fade-in transition-opacity duration-500">
        {loadingMessages[messageIndex]}
      </p>
    </div>
  )
}
