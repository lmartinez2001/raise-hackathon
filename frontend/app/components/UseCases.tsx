import { Users, ClipboardCheck, FlaskConical, Share2 } from "lucide-react"

const useCases = [
  {
    title: "Enable Info Sharing Across the Org",
    description: "Improving efficiency of the whole org by reducing time spent digging for info.",
    icon: Share2,
  },
  {
    title: "Faster Onboarding",
    description:
      "Help new hires get up to speed by asking questions about past projects, decisions, and team processes.",
    icon: Users,
  },
  {
    title: "Project Alignment",
    description: "Keep teams aligned by easily tracking decisions and action items across long-running projects.",
    icon: ClipboardCheck,
  },
  {
    title: "Technical Deep Dives",
    description:
      "Engineers can instantly find technical discussions, architectural decisions, and shared research papers.",
    icon: FlaskConical,
  },
]

export default function UseCases() {
  return (
    <section id="use-cases" className="w-full py-16 md:py-24 bg-slate-100">
      <div className="container mx-auto px-4 md:px-6">
        <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl text-center mb-12">
          How Teams Use Contexta
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {useCases.map((useCase, index) => (
            <div key={index} className="flex flex-col items-center text-center p-6 bg-white rounded-lg shadow-md">
              <useCase.icon className="h-12 w-12 mb-4 text-purple-600" />
              <h3 className="text-xl font-bold mb-2">{useCase.title}</h3>
              <p className="text-gray-600">{useCase.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
