import { type NextRequest, NextResponse } from "next/server"

// Bring your Flask backend URL from env, fallback to localhost:5049 if not set
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5049/api"

export async function POST(request: NextRequest) {
  try {
    // Read the incoming request body
    const body = await request.json()

    // Forward the request to your Flask backend's /api/recommend endpoint
    const flaskResponse = await fetch(`${API_URL}/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    })

    // Parse the response JSON
    const data = await flaskResponse.json()

    // Return what Flask sends, forwarding the status too
    return NextResponse.json(data, { status: flaskResponse.status })
  } catch (error) {
    return NextResponse.json(
      { error: "Backend Flask API unreachable or error" },
      { status: 502 }
    )
  }
}
