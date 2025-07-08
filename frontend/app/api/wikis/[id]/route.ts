import { NextResponse } from "next/server"
import { mockWikis } from "@/app/lib/mock-wikis"
import type { Wiki } from "@/app/lib/mock-wikis"

export async function GET(request: Request, { params }: { params: { id: string } }) {
  // --- PREVIEW-FRIENDLY DATA FETCHING ---
  // In a preview environment, params.id might not be a valid ID from our mock data.
  // To prevent a 404 error during preview, we first try to find the specific wiki.
  // If it's not found, we fall back to the first wiki in the mock array as a default.
  let wiki: Wiki | undefined = mockWikis.find((w) => w.id === params.id)

  if (!wiki) {
    // Fallback for previewing purposes
    wiki = mockWikis[0]
  }

  // If after the fallback, there's still no wiki, then return a 404.
  if (!wiki) {
    return NextResponse.json({ error: "Wiki not found" }, { status: 404 })
  }

  return NextResponse.json(wiki)
}
