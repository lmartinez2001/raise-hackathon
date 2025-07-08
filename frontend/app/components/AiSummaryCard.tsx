"use client"

import type React from "react"
import { useRef, useEffect } from "react"
import { Bot, Send, MessageSquarePlus, User, Video, FileText, MessageSquare, Library } from "lucide-react"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { Avatar } from "@/components/ui/avatar"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Logo } from "./Logo"

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

interface AiSummaryCardProps {
  messages: Message[]
  inputValue: string
  onInputChange: (value: string) => void
  onSendMessage: () => void
  isExpanded: boolean
  onExpansionChange: (isExpanded: boolean) => void
}

const SourcePill = ({ source, onClick }: { source: SourceReference; onClick: (id: string) => void }) => (
  <div
    onClick={() => onClick(source.id)}
    className="flex-shrink-0 flex items-center gap-1 bg-slate-100 hover:bg-slate-200 transition-colors cursor-pointer rounded-md px-1.5 py-0.5 text-[11px]"
  >
    {source.type === "meeting" && <Video className="h-3 w-3 text-orange-600 flex-shrink-0" />}
    {source.type === "document" && <FileText className="h-3 w-3 text-blue-600 flex-shrink-0" />}
    {source.type === "slack" && <MessageSquare className="h-3 w-3 text-purple-600 flex-shrink-0" />}
    {source.type === "wiki" && <Library className="h-3 w-3 text-green-600 flex-shrink-0" />}
    <span className="text-slate-700 font-medium truncate" style={{ maxWidth: "120px" }}>
      {source.title}
    </span>
  </div>
)

export default function AiSummaryCard({
  messages,
  inputValue,
  onInputChange,
  onSendMessage,
  isExpanded,
  onExpansionChange,
}: AiSummaryCardProps) {
  const cardRef = useRef<HTMLDivElement>(null)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      onSendMessage()
    }
  }

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (cardRef.current && !cardRef.current.contains(event.target as Node)) {
        const target = event.target as HTMLElement
        if (!target.closest('[data-suggested-question="true"]')) {
          onExpansionChange(false)
        }
      }
    }
    if (isExpanded) {
      document.addEventListener("mousedown", handleClickOutside)
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [isExpanded, onExpansionChange])

  const handleSourceClick = (sourceId: string) => {
    const element = document.getElementById(sourceId)
    if (element) {
      const header = document.querySelector("header")
      const searchBar = document.getElementById("sticky-search-bar")

      let offset = 16 // 1rem extra padding
      if (header) {
        offset += header.offsetHeight
      }
      if (searchBar) {
        offset += searchBar.offsetHeight
      }

      const elementPosition = element.getBoundingClientRect().top
      const offsetPosition = elementPosition + window.scrollY - offset

      window.scrollTo({
        top: offsetPosition,
        behavior: "smooth",
      })

      // Highlight logic remains the same
      element.classList.add("ring-2", "ring-blue-500", "ring-offset-2", "transition-all", "duration-300")
      setTimeout(() => {
        element.classList.remove("ring-2", "ring-blue-500", "ring-offset-2")
      }, 2000)
    }
  }

  return (
    <Card
      ref={cardRef}
      className="bg-white shadow-lg rounded-xl border-t-4 border-blue-500 overflow-hidden flex flex-col max-h-[70vh]"
    >
      <CardHeader className="flex flex-row items-center space-x-3 pb-2 flex-shrink-0">
        <div className="h-8 w-8 flex-shrink-0 flex items-center justify-center bg-blue-500 rounded-md">
          <Bot className="h-5 w-5 text-white" />
        </div>
        <CardTitle className="text-base font-semibold">Assistant Summary</CardTitle>
      </CardHeader>
      <CardContent ref={scrollAreaRef} className="flex-grow space-y-4 overflow-y-auto">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex items-start gap-3 animate-fade-in",
              message.role === "user" ? "justify-end" : "justify-start",
            )}
          >
            {message.role === "assistant" && (
              <Avatar className="h-8 w-8 flex-shrink-0 border bg-white p-0.5">
                <Logo className="h-full w-full" />
              </Avatar>
            )}
            <div
              className={cn(
                "max-w-xl",
                message.role === "user"
                  ? "bg-slate-200 text-slate-800 p-3 rounded-lg rounded-br-none shadow-sm"
                  : "text-gray-700 pt-1",
              )}
            >
              <p className="text-sm leading-normal">{message.content}</p>
              {message.role === "assistant" && message.sources && message.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-200">
                  <h4 className="text-xs font-semibold text-slate-500 mb-2">Sources</h4>
                  <TooltipProvider delayDuration={100}>
                    <div className="flex items-center gap-1.5 overflow-hidden">
                      {message.sources.slice(0, 3).map((source) => (
                        <SourcePill key={source.id} source={source} onClick={handleSourceClick} />
                      ))}
                      {message.sources.length > 3 && (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <div className="flex-shrink-0 flex items-center justify-center bg-slate-200 hover:bg-slate-300 transition-colors cursor-pointer rounded-md px-1.5 py-0.5 text-[11px] font-medium text-slate-600">
                              +{message.sources.length - 3} more
                            </div>
                          </TooltipTrigger>
                          <TooltipContent>
                            <div className="flex flex-col gap-1.5 p-1">
                              {message.sources.slice(3).map((source) => (
                                <SourcePill key={source.id} source={source} onClick={handleSourceClick} />
                              ))}
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      )}
                    </div>
                  </TooltipProvider>
                </div>
              )}
            </div>
            {message.role === "user" && (
              <Avatar className="h-8 w-8 flex-shrink-0">
                <div className="h-full w-full flex items-center justify-center bg-slate-200 rounded-full">
                  <User className="h-5 w-5 text-slate-600" />
                </div>
              </Avatar>
            )}
          </div>
        ))}
      </CardContent>
      <CardFooter className="p-3 bg-slate-50/70 border-t flex-shrink-0">
        {isExpanded ? (
          <div className="w-full relative">
            <Input
              placeholder="To clear this chat history, ask a new question in the top search bar..."
              value={inputValue}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={handleKeyPress}
              className="h-12 pr-12 text-sm bg-white placeholder:text-slate-400"
              autoFocus
            />
            <Button
              size="icon"
              onClick={onSendMessage}
              disabled={inputValue.trim() === ""}
              className={cn(
                "absolute right-2 top-1/2 -translate-y-1/2 h-9 w-9 rounded-full transition-all",
                inputValue.trim() !== ""
                  ? "bg-blue-500 text-white hover:bg-blue-600 scale-100"
                  : "bg-gray-200 text-gray-400 scale-95",
              )}
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <div className="w-full flex justify-start">
            <Button
              variant="outline"
              className="rounded-full bg-white/80 backdrop-blur-sm shadow-sm hover:bg-gray-100 hover:border-gray-400 transition-all group"
              onClick={() => onExpansionChange(true)}
            >
              <MessageSquarePlus className="h-4 w-4 mr-2 text-gray-500 group-hover:text-gray-700" />
              Ask another question
            </Button>
          </div>
        )}
      </CardFooter>
    </Card>
  )
}
