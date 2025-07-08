import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
    if (request.nextUrl.pathname.startsWith('/dashboard')) {
        try {
            console.log(process.env.NEXT_PUBLIC_FRONTEND_URL);

            const response = await fetch(`${process.env.NEXT_PUBLIC_FRONTEND_URL}/api/auth/status`, {
                headers: {
                    'Cookie': request.headers.get('cookie') || '',
                },
            })

            if (!response.ok) {
                return NextResponse.redirect(new URL('/', request.url))
            }

            const authData = await response.json()

            if (!authData.authenticated) {
                return NextResponse.redirect(new URL('/', request.url))
            }
        } catch {
            return NextResponse.redirect(new URL('/', request.url))
        }
    }

    return NextResponse.next()
}

export const config = {
    matcher: '/dashboard/:path*',
}