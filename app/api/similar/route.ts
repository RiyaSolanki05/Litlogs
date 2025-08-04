import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.FLASK_API_URL || 'http://localhost:5049/api';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const bookId = searchParams.get('book_id');

  if (!bookId) {
    return NextResponse.json({ books: [] });
  }

  try {
    // Fetch similar books from Flask backend
    const res = await fetch(`${API_BASE_URL}/similar?book_id=${encodeURIComponent(bookId)}`);
    if (!res.ok) {
      return NextResponse.json({ books: [] });
    }
    const data = await res.json();
    return NextResponse.json({ books: data.books || [] });
  } catch (error) {
    return NextResponse.json({ books: [] });
  }
}
