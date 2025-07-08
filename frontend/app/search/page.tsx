import { Suspense } from "react"
import Header from "../components/Header"
import Footer from "../components/Footer"
import SearchResultsClient from "./search-results-client"
import SearchLoading from "../components/SearchLoading"

export default function SearchPage() {
  return (
    <div className="flex flex-col min-h-screen bg-slate-50">
      <Header />
      <main className="flex-grow">
        <Suspense fallback={<SearchLoading />}>
          <SearchResultsClient />
        </Suspense>
      </main>
      <Footer />
    </div>
  )
}
