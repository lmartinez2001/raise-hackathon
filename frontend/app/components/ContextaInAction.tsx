import ActionDemo from "./ActionDemo"

export default function ContextaInAction() {
  return (
    <section id="demo" className="w-full py-16 md:py-24 bg-white">
      <div className="container mx-auto px-4 md:px-6">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">See Contexta in Action</h2>
          <p className="mx-auto max-w-[700px] text-gray-600 md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed dark:text-gray-300 mt-4">
            Watch how Contexta easily unlocks info for your team by pulling a comprehensive summary from multiple
            sources in real-time.
          </p>
        </div>
        <div className="relative mt-12">
          <div className="absolute top-1/2 -left-4 w-72 h-72 bg-blue-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
          <div className="absolute top-1/2 -right-4 w-72 h-72 bg-purple-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
          <div className="relative max-w-5xl mx-auto">
            <ActionDemo />
          </div>
        </div>
      </div>
    </section>
  )
}
