import { NextResponse } from "next/server"

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const resolvedParams = await params
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000"
    const response = await fetch(`${backendUrl}/api/wikis/${resolvedParams.id}`)

    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json({ error: "Wiki not found" }, { status: 404 })
      }
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    const wiki = await response.json()
    return NextResponse.json(wiki)
  } catch (error) {
    console.error("Error fetching wiki from backend:", error)
    return NextResponse.json({ error: "Failed to fetch wiki" }, { status: 500 })
  }
}
