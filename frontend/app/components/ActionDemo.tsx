import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Search } from "lucide-react"
import AiSummaryCard from "./AiSummaryCard"
import SuggestedQuestions from "./SuggestedQuestions"
import SourceStream from "./SourceStream"
import { mockSources } from "../lib/mock-data"

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
          <AiSummaryCard />
          <SuggestedQuestions />
          <SourceStream sources={mockSources} />
        </div>
      </CardContent>
    </Card>
  )
}
