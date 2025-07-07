"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { GoogleIcon } from "../components/GoogleIcon"
import GoogleLoginModal from "../components/GoogleLoginModal"

export default function LoginPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)

  async function handleGoogleLogin() {
    try {
      // Instead of fetch, directly redirect to the backend login endpoint
      window.location.href = "/api/auth/login"
    } catch (err) {
      console.error(err)
      alert("Login failed; check console for details.")
    }
  }

  return (
    <>
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 p-4">
        <div className="absolute top-6 left-6 md:top-8 md:left-8">
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
        </div>
        <Card className="w-full max-w-sm mx-auto shadow-lg">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">Welcome Back</CardTitle>
            <CardDescription>Sign in to connect your workspace and unlock your team's knowledge.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Button
                variant="outline"
                className="w-full h-12 text-base font-medium bg-transparent"
                onClick={handleGoogleLogin}
              >
                <GoogleIcon className="mr-3 h-6 w-6" />
                Sign in with Google
              </Button>
            </div>
            <p className="mt-6 px-8 text-center text-xs text-muted-foreground">
              By signing in, you agree to our{" "}
              <Link href="#" className="underline underline-offset-4 hover:text-primary">
                Terms of Service
              </Link>{" "}
              and{" "}
              <Link href="#" className="underline underline-offset-4 hover:text-primary">
                Privacy Policy
              </Link>
              .
            </p>
          </CardContent>
        </Card>
      </div>
      <GoogleLoginModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </>
  )
}
