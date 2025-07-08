// --- DATA-DRIVEN COMPONENTS ---
// These components are designed to be "presentational" or "dumb". They receive data
// as props and render it without containing any business logic themselves.
//
// To integrate with a real database:
// 1. Your API should return data that conforms to the `MeetingSource`, `SlackSource`,
//    `DocumentSource`, and `WikiSource` interfaces defined in `app/lib/mock-data.ts`.
// 2. The parent component (`SourceStream.tsx`) will pass the correctly-typed props
//    to these card components.
//
// No changes are needed in this file to support real data, as long as the
// data contract is respected by the API.

import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  FileText,
  MessageSquare,
  Video,
  ExternalLink,
  Github,
  FileType,
  PlayCircle,
  Notebook,
  Library,
} from "lucide-react"
import Link from "next/link"
import type { MeetingSource, SlackSource, DocumentSource, WikiSource } from "../lib/mock-data"

export function MeetingCard({ id, title, timestamp, transcriptSnippet, link }: MeetingSource) {
  return (
    <Card id={id} className="bg-white shadow-sm rounded-xl overflow-hidden">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base font-semibold">
          <div className="flex-shrink-0 h-8 w-8 flex items-center justify-center rounded-md bg-orange-100">
            <Video className="h-4 w-4 text-orange-600" />
          </div>
          <span>{title}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-2">
        <p className="text-xs font-medium text-gray-600 mb-2">At {timestamp} – Discussion on data privacy</p>
        <blockquote className="border-l-2 border-orange-200 pl-3 text-sm text-gray-600 italic">
          {transcriptSnippet}
        </blockquote>
      </CardContent>
      <CardFooter className="flex flex-wrap justify-start items-center bg-gray-50/50 p-3 gap-x-4 gap-y-2">
        <Link href={link} className="text-xs text-blue-600 hover:underline flex items-center gap-1.5">
          Full transcript <ExternalLink className="h-3 w-3" />
        </Link>
        <Link href={link} className="text-xs text-blue-600 hover:underline flex items-center gap-1.5">
          View video <PlayCircle className="h-3 w-3" />
        </Link>
        <Link href={link} className="text-xs text-blue-600 hover:underline flex items-center gap-1.5">
          View meeting note <Notebook className="h-3 w-3" />
        </Link>
      </CardFooter>
    </Card>
  )
}

export function SlackCard({ id, channel, author, avatar, message, attachment }: SlackSource) {
  return (
    <Card id={id} className="bg-white shadow-sm rounded-xl overflow-hidden">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base font-semibold">
          <div className="flex-shrink-0 h-8 w-8 flex items-center justify-center rounded-md bg-purple-100">
            <MessageSquare className="h-4 w-4 text-purple-600" />
          </div>
          <span>Slack thread from #{channel}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-2 pb-4">
        <div className="flex items-start gap-3">
          <Avatar className="h-8 w-8">
            <AvatarImage src={avatar || "/placeholder.svg"} alt={author} />
            <AvatarFallback>{author.charAt(0)}</AvatarFallback>
          </Avatar>
          <div>
            <p className="text-sm font-semibold">{author}</p>
            <p className="text-sm text-gray-600">{message}</p>
          </div>
        </div>
        {attachment && (
          <Card className="mt-3 bg-slate-50">
            <CardContent className="p-2 flex items-center gap-2">
              {attachment.type === "github" ? (
                <Github className="h-4 w-4 text-gray-600" />
              ) : (
                <FileType className="h-4 w-4 text-gray-600" />
              )}
              <div>
                <p className="font-medium text-xs">{attachment.title}</p>
                <p className="text-xs text-gray-500">{attachment.description}</p>
              </div>
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  )
}

export function DocumentCard({ id, title, author, updated, snippet, link }: DocumentSource) {
  return (
    <Card id={id} className="bg-white shadow-sm rounded-xl overflow-hidden">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base font-semibold">
          <div className="flex-shrink-0 h-8 w-8 flex items-center justify-center rounded-md bg-blue-100">
            <FileText className="h-4 w-4 text-blue-600" />
          </div>
          <span>{title}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-2">
        <p className="text-xs text-gray-500 mb-2">
          By {author} · Last updated {updated}
        </p>
        <p className="text-sm text-gray-600">"...{snippet}..."</p>
      </CardContent>
      <CardFooter className="bg-gray-50/50 p-3">
        <Link href={link} className="text-xs text-blue-600 hover:underline flex items-center gap-1">
          See in full doc <ExternalLink className="h-3 w-3" />
        </Link>
      </CardFooter>
    </Card>
  )
}

export function WikiCard({ id, title, snippet, link }: WikiSource) {
  return (
    <Card id={id} className="bg-white shadow-sm rounded-xl overflow-hidden">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base font-semibold">
          <div className="flex-shrink-0 h-8 w-8 flex items-center justify-center rounded-md bg-green-100">
            <Library className="h-4 w-4 text-green-600" />
          </div>
          <span>{title}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-2">
        <p className="text-sm text-gray-600">"...{snippet}..."</p>
      </CardContent>
      <CardFooter className="bg-gray-50/50 p-3">
        <Link href={link} className="text-xs text-blue-600 hover:underline flex items-center gap-1">
          View full wiki <ExternalLink className="h-3 w-3" />
        </Link>
      </CardFooter>
    </Card>
  )
}
