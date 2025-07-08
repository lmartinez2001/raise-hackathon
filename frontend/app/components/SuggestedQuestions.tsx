"use client"

import { Button } from "@/components/ui/button"

interface SuggestedQuestionsProps {
  questions: string[]
  onQuestionClick: (question: string) => void
}

export default function SuggestedQuestions({ questions, onQuestionClick }: SuggestedQuestionsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {questions.map((q, i) => (
        <Button
          key={i}
          variant="outline"
          size="sm"
          className="rounded-full bg-white shadow-sm hover:bg-gray-100 hover:border-gray-400 transition-all"
          onClick={() => onQuestionClick(q)}
          data-suggested-question="true"
        >
          {q}
        </Button>
      ))}
    </div>
  )
}
