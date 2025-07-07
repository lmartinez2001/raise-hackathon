import { Sparkles, BrainCircuit, MessageSquare, Files } from "lucide-react"

const features = [
  {
    title: "Unified Search",
    description: "One search bar to find answers across all your meetings, documents, and chats.",
    icon: Sparkles,
  },
  {
    title: "Multi-Meeting Intelligence",
    description: "Synthesize discussions and decisions that span across multiple related meetings.",
    icon: BrainCircuit,
  },
  {
    title: "Slack & Docs Integration",
    description: "Connect conversations and shared files from Slack and Google Drive to your search.",
    icon: MessageSquare,
  },
  {
    title: "Traceable Sources",
    description: "Every insight is linked back to its source—video timestamps, doc passages, and chat messages.",
    icon: Files,
  },
]

export default function Features() {
  return (
    <section id="features" className="w-full py-16 md:py-24 bg-white">
      <div className="container mx-auto px-4 md:px-6">
        <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-center mb-12">
          A Smarter Way to Access Knowledge
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="flex flex-col items-center text-center p-6 bg-slate-50 rounded-lg shadow-sm">
              <feature.icon className="h-12 w-12 mb-4 text-blue-600" />
              <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
              <p className="text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
