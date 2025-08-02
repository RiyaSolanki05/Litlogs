import { type NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5049/api";

export async function POST(request: NextRequest) {
  try {
    const { message } = await request.json();

    if (!message) {
      return NextResponse.json({
        message: "Please provide a message for book recommendations.",
        books: [],
      });
    }

    // Send the query to your Flask backend (you may have a dedicated /api/chatbot endpoint,
    // or just /recommend for smart routing)
    const res = await fetch(`${API_URL}/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: message, top_n: 5 }),
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      return NextResponse.json({
        message:
          data?.error || "Sorry, I encountered an error processing your request.",
        books: [],
      }, { status: 500 });
    }

    const data = await res.json();

    // You can craft a natural-language response here if desired, or let your Flask backend do it.
    return NextResponse.json({
      message: data?.books?.length
        ? "Here are some recommendations based on your request:"
        : "Sorry, no recommendations were found.",
      books: data?.books || [],
    });
  } catch (error) {
    console.error("Chat API error:", error);
    return NextResponse.json(
      {
        message: "Sorry, I encountered an error processing your request.",
        books: [],
      },
      { status: 500 }
    );
  }
}
