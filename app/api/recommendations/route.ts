import { type NextRequest, NextResponse } from "next/server"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5049/api";

interface RecommendationRequest {
  type: "title" | "genre" | "author" | "keywords" | "filters"
  query: string
  filters?: {
    genre?: string
    year?: number
    mood?: string[]
  }
  limit?: number
}

/**
 * Routes incoming rec requests to the correct backend endpoint.
 */
export async function POST(request: NextRequest) {
  try {
    const body: RecommendationRequest = await request.json();
    const { type, query, filters, limit = 10 } = body;

    let endpoint = `${API_URL}/recommend`; // default: uses smart router in Flask
    let payload: any = { query, top_n: limit };

    // Route to specific backend endpoints for tighter control
    switch (type) {
      case "genre":
        endpoint = `${API_URL}/recommend/genre`;
        payload = { genre: query, top_n: limit };
        break;
      case "author":
        endpoint = `${API_URL}/recommend/author`;
        payload = { author: query, top_n: limit };
        break;
      case "title":
        endpoint = `${API_URL}/recommend/title`;
        payload = { title: query, top_n: limit };
        break;
      case "keywords":
        endpoint = `${API_URL}/recommend/keywords`;
        payload = { keywords: Array.isArray(query) ? query : [query], top_n: limit };
        break;
      case "filters":
        endpoint = `${API_URL}/recommend/filters`;
        payload = {
          genre: filters?.genre || undefined,
          year: filters?.year || undefined,
          mood_keywords: filters?.mood || undefined,
          top_n: limit
        };
        break;
      default:
        // Fallback to smart router
        endpoint = `${API_URL}/recommend`;
        payload = { query, top_n: limit };
    }

    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();

    // Return unified shape
    return NextResponse.json({
      recommendations: data.books || [],
      total: (data.books || []).length,
      query,
      type,
      ...(data.error ? { error: data.error } : {})
    }, { status: res.ok ? 200 : 400 });

  } catch (error) {
    console.error("Recommendations API error:", error);
    return NextResponse.json(
      { error: "Failed to get recommendations" },
      { status: 500 }
    );
  }
}
