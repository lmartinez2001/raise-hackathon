import { Button } from "@/components/ui/button"

export default function SuggestedQuestions() {
  const questions = [
    "What actions were assigned to me?",
    "Was there any disagreement?",
    "Any related updates shared after the meeting?",
  ]
  return (
    <div className="flex flex-wrap gap-3">
      {questions.map((q, i) => (
        <Button
          key={i}
          variant="outline"
          className="rounded-full bg-white shadow-sm hover:bg-gray-100 hover:border-gray-400 transition-all"
        >
          {q}
        </Button>
      ))}
    </div>
  )
}
