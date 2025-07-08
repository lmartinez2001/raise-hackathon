import Link from "next/link"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"

interface Wiki {
  id: string
  title: string
  summary: string
  href: string
}

export default function WikiCard({ wiki }: { wiki: Wiki }) {
  return (
    <Card className="flex flex-col bg-white shadow-md hover:shadow-xl transition-shadow duration-300 rounded-lg">
      <CardHeader>
        <CardTitle className="text-lg font-bold">{wiki.title}</CardTitle>
      </CardHeader>
      <CardContent className="flex-grow">
        <p className="text-sm text-gray-600 leading-relaxed">{wiki.summary}</p>
      </CardContent>
      <CardFooter className="flex justify-end pt-4">
        <Link href={wiki.href} passHref>
          <Button variant="ghost" size="sm">
            View Wiki
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </Link>
      </CardFooter>
    </Card>
  )
}
