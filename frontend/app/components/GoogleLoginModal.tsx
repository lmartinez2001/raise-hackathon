"use client"
import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { GoogleIcon } from "./GoogleIcon"
import { X } from "lucide-react"

interface GoogleLoginModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function GoogleLoginModal({ isOpen, onClose }: GoogleLoginModalProps) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  if (!isOpen) return null

  const handleClose = () => {
    setEmail("")
    setPassword("")
    onClose()
  }

  const handleSignIn = () => {
    // Placeholder for sign-in logic
    console.log("Signing in with:", email, password)
    handleClose()
  }

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center animate-fade-in p-4">
      <Card className="w-full max-w-sm relative animate-fade-in">
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-2 right-2 text-muted-foreground"
          onClick={handleClose}
        >
          <X className="h-5 w-5" />
          <span className="sr-only">Close</span>
        </Button>
        <CardHeader className="text-center pt-8">
          <div className="flex justify-center mb-4">
            <GoogleIcon className="h-8 w-8" />
          </div>
          <CardTitle className="text-2xl">Sign in</CardTitle>
          <CardDescription>to continue to Contexta</CardDescription>
        </CardHeader>
        <CardContent className="px-8">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email or phone</Label>
              <Input
                id="email"
                type="email"
                placeholder="Email or phone"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-12 text-base"
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-12 text-base"
              />
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col px-8 pb-8">
          <div className="w-full flex justify-between items-center mt-8">
            <Button variant="link" className="p-0 text-blue-600 font-medium">
              Create account
            </Button>
            <Button onClick={handleSignIn} disabled={!email || !password}>
              Sign In
            </Button>
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}
