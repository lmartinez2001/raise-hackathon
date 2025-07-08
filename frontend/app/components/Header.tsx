"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Logo } from "./Logo"
import { Library } from "lucide-react"

export default function Header() {
  const pathname = usePathname()
  const isLoggedIn = ["/dashboard", "/search", "/wikis"].some((path) => pathname.startsWith(path))
  const logoHref = isLoggedIn ? "/dashboard" : "/"

  return (
    <header className="w-full px-4 lg:px-6 h-16 flex items-center border-b bg-white/80 backdrop-blur-sm sticky top-0 z-20">
      <Link href={logoHref} className="flex items-center gap-2.5">
        <Logo className="h-7 w-7" />
        <span className="text-2xl font-bold text-gray-900 tracking-tight">Contexta</span>
      </Link>
      <nav className="ml-auto flex items-center gap-4">
        <Button asChild variant="ghost" className="text-gray-600">
          <Link href="/wikis" className="flex items-center gap-1.5 text-sm font-medium">
            <Library className="h-4 w-4" />
            Wikis
          </Link>
        </Button>
      </nav>
    </header>
  )
}
