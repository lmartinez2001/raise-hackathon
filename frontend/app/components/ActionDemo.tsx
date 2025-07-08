import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Search } from "lucide-react"
import AiSummaryCard from "./AiSummaryCard"
import SuggestedQuestions from "./SuggestedQuestions"
import SourceStream from "./SourceStream"
import { mockSources } from "../lib/mock-data"

const demoMessages = [
  {
    id: "demo-1",
    role: "assistant" as const,
    content:
      'In the Q2 planning meetings, the primary data privacy concerns revolved around GDPR compliance for new European markets. The team discussed potential vulnerabilities in the user data encryption methods, as noted in the "Project Titan Security Review" document. A follow-up action was assigned to Sarah in the #security Slack channel to investigate third-party vendor compliance, and this was also touched upon in the earlier Q2 planning session.',
    sources: [
      { id: "meeting-1", type: "meeting", title: "Q2 Product Sync – June 18" },
      { id: "doc-1", type: "document", title: "Project Titan Security Review" },
      { id: "slack-1", type: "slack", title: "Slack thread from #security" },
      { id: "meeting-2", type: "meeting", title: "Q2 Planning (Part 1) – June 12" },
    ],
  },
  {
    id: "demo-2",
    role: "user" as const,
    content: "Was there any disagreement?",
  },
  {
    id: "demo-3",
    role: "assistant" as const,
    content:
      "Yes, there was a disagreement regarding the implementation timeline for the new encryption keys, but not the necessity of the keys themselves.",
    sources: [{ id: "doc-1", type: "document", title: "Project Titan Security Review" }],
  },
]

const demoSuggestedQuestions = [
  "Who was involved in the disagreement?",
  "What was the proposed timeline?",
  "Summarize Alex Chen's point.",
]

export default function ActionDemo() {
  return (
    <Card className="shadow-2xl rounded-2xl overflow-hidden border-4 border-gray-200/50">
      <CardHeader className="bg-gray-100 p-4 border-b">
        <div className="relative rounded-lg border bg-white p-3 flex items-center gap-3 shadow-sm">
          <Search className="h-5 w-5 text-gray-500" />
          <p className="text-gray-900 font-medium">
            What were the concerns around data privacy in our Q2 planning meetings?
          </p>
        </div>
      </CardHeader>
      <CardContent className="p-6 space-y-6 max-h-[60vh] overflow-y-auto bg-slate-50">
        <div className="space-y-8">
          <AiSummaryCard
            messages={demoMessages}
            inputValue=""
            onInputChange={() => {}}
            onSendMessage={() => {}}
            isReplying={true} // isReplying is true to disable the button in the demo
            isExpanded={false}
            onExpansionChange={() => {}}
          />
          <SuggestedQuestions questions={demoSuggestedQuestions} onQuestionClick={() => {}} />
          <SourceStream sources={mockSources} />
        </div>
      </CardContent>
    </Card>
  )
}
