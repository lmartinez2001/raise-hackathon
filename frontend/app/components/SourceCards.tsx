import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { FileText, MessageSquare, Video, ExternalLink, Github, FileType } from "lucide-react"
import Link from "next/link"
import type { MeetingSource, SlackSource, DocumentSource } from "../lib/mock-data"

export function MeetingCard({ title, timestamp, transcriptSnippet, tags, link }: MeetingSource) {
  return (
    <Card className="bg-white shadow-sm rounded-xl overflow-hidden">
      <CardHeader>
        <CardTitle className="flex items-center gap-3">
          <Video className="h-5 w-5 text-orange-500" />
          <span>{title}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm font-semibold text-gray-800 mb-2">At {timestamp} – Discussion on data privacy</p>
        <blockquote className="border-l-4 border-orange-200 pl-4 text-gray-600 italic">{transcriptSnippet}</blockquote>
      </CardContent>
      <CardFooter className="flex justify-between items-center bg-gray-50/50 p-4">
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <Badge key={tag} variant="outline">
              #{tag}
            </Badge>
          ))}
        </div>
        <Link href={link} className="text-sm text-blue-600 hover:underline flex items-center gap-1">
          Full transcript <ExternalLink className="h-3 w-3" />
        </Link>
      </CardFooter>
    </Card>
  )
}

export function SlackCard({ channel, author, avatar, message, attachment, link, tags }: SlackSource) {
  return (
    <Card className="bg-white shadow-sm rounded-xl overflow-hidden">
      <CardHeader>
        <CardTitle className="flex items-center gap-3">
          <MessageSquare className="h-5 w-5 text-purple-500" />
          <span>Slack thread from #{channel}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-start gap-3">
          <Avatar>
            <AvatarImage src={avatar || "/placeholder.svg"} alt={author} />
            <AvatarFallback>{author.charAt(0)}</AvatarFallback>
          </Avatar>
          <div>
            <p className="font-semibold">{author}</p>
            <p className="text-gray-600">{message}</p>
          </div>
        </div>
        {attachment && (
          <Card className="mt-4 bg-slate-50">
            <CardContent className="p-3 flex items-center gap-3">
              {attachment.type === "github" ? (
                <Github className="h-5 w-5 text-gray-600" />
              ) : (
                <FileType className="h-5 w-5 text-gray-600" />
              )}
              <div>
                <p className="font-medium text-sm">{attachment.title}</p>
                <p className="text-xs text-gray-500">{attachment.description}</p>
              </div>
            </CardContent>
          </Card>
        )}
      </CardContent>
      <CardFooter className="flex justify-between items-center bg-gray-50/50 p-4">
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <Badge key={tag} variant="outline">
              #{tag}
            </Badge>
          ))}
        </div>
        <Link href={link} className="text-sm text-blue-600 hover:underline flex items-center gap-1">
          View on Slack <ExternalLink className="h-3 w-3" />
        </Link>
      </CardFooter>
    </Card>
  )
}

export function DocumentCard({ title, author, updated, snippet, link }: DocumentSource) {
  return (
    <Card className="bg-white shadow-sm rounded-xl overflow-hidden">
      <CardHeader>
        <CardTitle className="flex items-center gap-3">
          <FileText className="h-5 w-5 text-blue-500" />
          <span>{title}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-gray-500 mb-2">
          By {author} · Last updated {updated}
        </p>
        <p className="text-gray-600">"...{snippet}..."</p>
      </CardContent>
      <CardFooter className="bg-gray-50/50 p-4">
        <Link href={link} className="text-sm text-blue-600 hover:underline flex items-center gap-1">
          See in full doc <ExternalLink className="h-3 w-3" />
        </Link>
      </CardFooter>
    </Card>
  )
}
