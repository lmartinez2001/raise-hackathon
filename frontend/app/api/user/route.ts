export async function GET(request: Request) {
    try {
        // Forward cookies from the browser to the backend
        const cookieHeader = request.headers.get('cookie') || '';

        // Call the backend API to get user info
        const backendUrl = process.env.BACKEND_URL || "http://localhost:8000"
        const response = await fetch(`${backendUrl}/api/user`, {
            headers: {
                'Content-Type': 'application/json',
                'Cookie': cookieHeader,
            },
        });

        if (!response.ok) {
            return Response.json({ error: 'Failed to fetch user info' }, { status: response.status });
        }

        const userData = await response.json();
        return Response.json(userData);
    } catch (error) {
        console.error('Error fetching user info:', error);
        return Response.json({ error: 'Internal server error' }, { status: 500 });
    }
}
