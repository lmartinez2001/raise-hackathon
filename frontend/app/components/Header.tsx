import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function Header() {
  return (
    <header className="w-full px-4 lg:px-6 h-16 flex items-center border-b bg-white/80 backdrop-blur-sm sticky top-0 z-20">
      <Link href="/" className="flex items-center gap-2.5">
        <svg width="28" height="28" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="4" y="8" width="20" height="20" rx="4" fill="#60A5FA" fillOpacity="0.6" />
          <rect x="8" y="4" width="20" height="20" rx="4" fill="#A78BFA" fillOpacity="0.6" />
          <g stroke="#0F172A" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none">
            <circle cx="16" cy="16" r="5" />
            <path d="M19.5 19.5 L 23 23" />
          </g>
        </svg>
        <span className="text-2xl font-bold text-gray-900 tracking-tight">Contexta</span>
      </Link>
      <div className="ml-auto">
        <Link href="/login">
          <Button variant="outline">Log In</Button>
        </Link>
      </div>
    </header>
  )
}
