import { Sparkles, BrainCircuit, FolderKanban, Files } from "lucide-react"

const features = [
  {
    title: "Cross-Source Unified Search",
    description: "One click to find answers across all your meetings, docs, and chats. No more context-switching.",
    icon: Sparkles,
  },
  {
    title: "Multi-Meeting Intelligence",
    description: "Meetings are fragmented by nature. Contexta aggregates discussions scattered across several syncs",
    icon: BrainCircuit,
  },
  {
    title: "No Manual Organization",
    description: "Say goodbye to the burden of never sorting post-meeting resources and copy & pasting from slack.",
    icon: FolderKanban,
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
