import { Bot, FileText, MessageSquare, Video } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function AiSummaryCard() {
  return (
    <Card className="bg-white shadow-lg rounded-xl border-t-4 border-blue-500">
      <CardHeader className="flex flex-row items-center space-x-4 pb-2">
        <div className="p-2 bg-primary/10 rounded-full">
          <Bot className="h-6 w-6 text-primary" />
        </div>
        <CardTitle className="text-lg font-semibold">Assistant Summary</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-gray-700 leading-relaxed">
          In the Q2 planning meetings, the primary data privacy concerns revolved around{" "}
          <a href="#" className="underline decoration-dotted hover:text-blue-600">
            GDPR compliance for new European markets
          </a>
          . The team discussed potential vulnerabilities in the user data encryption methods, as noted in the{" "}
          <a href="#" className="underline decoration-dotted hover:text-blue-600">
            "Project Titan Security Review" document
          </a>
          . A follow-up action was assigned to Sarah in the{" "}
          <a href="#" className="underline decoration-dotted hover:text-blue-600">
            #security Slack channel
          </a>{" "}
          to investigate third-party vendor compliance.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Badge variant="secondary" className="bg-blue-100 text-blue-800 hover:bg-blue-200 border-blue-200">
            <FileText className="h-3 w-3 mr-1.5" />
            Docs
          </Badge>
          <Badge variant="secondary" className="bg-purple-100 text-purple-800 hover:bg-purple-200 border-purple-200">
            <MessageSquare className="h-3 w-3 mr-1.5" />
            Slack Messages
          </Badge>
          <Badge variant="secondary" className="bg-orange-100 text-orange-800 hover:bg-orange-200 border-orange-200">
            <Video className="h-3 w-3 mr-1.5" />
            Meeting Recordings
          </Badge>
        </div>
      </CardContent>
    </Card>
  )
}
