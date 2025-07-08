import { MeetingCard, SlackCard, DocumentCard, WikiCard } from "./SourceCards"
import type { Source } from "../lib/mock-data"

interface SourceStreamProps {
  sources: Source[]
}

export default function SourceStream({ sources }: SourceStreamProps) {
  return (
    <div className="space-y-6">
      {sources.map((source) => {
        switch (source.type) {
          case "meeting":
            return <MeetingCard key={source.id} {...source} />
          case "slack":
            return <SlackCard key={source.id} {...source} />
          case "document":
            return <DocumentCard key={source.id} {...source} />
          case "wiki":
            return <WikiCard key={source.id} {...source} />
          default:
            return null
        }
      })}
    </div>
  )
}
