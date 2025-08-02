import { type NextRequest, NextResponse } from "next/server"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5049/api";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get("q")?.trim() || "";

  if (!query) {
    return NextResponse.json({ books: [] });
  }

  try {
    const res = await fetch(`${API_URL}/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return NextResponse.json({ books: [], error: err.error || "Server error" }, { status: 500 });
    }

    const data = await res.json();
    // shape: { books: [...] }
    return NextResponse.json({ books: data.books || [] });
  } catch (error) {
    return NextResponse.json({ books: [], error: "Connection error" }, { status: 500 });
  }
}
