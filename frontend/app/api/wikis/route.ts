import { NextResponse } from "next/server"
import { mockWikis } from "@/app/lib/mock-wikis"
import type { Wiki } from "@/app/lib/mock-wikis"

// --- INTEGRATION GUIDE ---
// This endpoint handles searching for wikis. In a real application, this would
// query your backend, which would then perform a full-text search on a database
// (like PostgreSQL, Elasticsearch) or a file system where your wikis are stored.

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const searchTerm = searchParams.get("q")?.toLowerCase()

  // --- REAL INTEGRATION POINT ---
  // Replace the mock logic with a fetch call to your FastAPI backend.
  /*
  try {
    const fastApiResponse = await fetch(`https://your-fastapi-backend.com/api/v1/wikis?q=${encodeURIComponent(searchTerm || '')}`);
    const wikis = await fastApiResponse.json();
    return NextResponse.json(wikis);
  } catch (error) {
    console.error("Error fetching wikis from backend:", error);
    return NextResponse.json({ error: "Failed to fetch wikis." }, { status: 500 });
  }
  */

  // --- FastAPI Backend Logic (/wikis) ---
  // 1.  Receive Search Term: Get the `q` parameter.
  // 2.  Database Query: Perform a full-text search (e.g., using `ILIKE` in SQL or a
  //     dedicated search index) on your wikis table/collection.
  // 3.  Return Results: Send back the array of matching wiki objects.

  if (!searchTerm) {
    return NextResponse.json(mockWikis)
  }

  const filteredWikis = mockWikis.filter((wiki: Wiki) => {
    return (
      wiki.title.toLowerCase().includes(searchTerm) ||
      wiki.summary.toLowerCase().includes(searchTerm) ||
      wiki.content.toLowerCase().includes(searchTerm) ||
      wiki.tags.some((tag) => tag.toLowerCase().includes(searchTerm))
    )
  })

  await new Promise((resolve) => setTimeout(resolve, 500))

  return NextResponse.json(filteredWikis)
}
