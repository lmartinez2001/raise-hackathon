import { NextResponse } from "next/server"

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const searchTerm = searchParams.get("q") || ""

  try {
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000"
    const response = await fetch(`${backendUrl}/api/wikis?q=${encodeURIComponent(searchTerm)}`)

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    const wikis = await response.json()
    return NextResponse.json(wikis)
  } catch (error) {
    console.error("Error fetching wikis from backend:", error)
    return NextResponse.json({ error: "Failed to fetch wikis" }, { status: 500 })
  }
}
