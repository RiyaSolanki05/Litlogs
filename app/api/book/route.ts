import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.FLASK_API_URL || 'http://localhost:5049/api';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const bookId = searchParams.get('book_id');

  if (!bookId) {
    return NextResponse.json({ error: 'Missing book_id parameter' }, { status: 400 });
  }

  try {
    // Fetch book detail from Flask backend
    const res = await fetch(`${API_BASE_URL}/book?book_id=${encodeURIComponent(bookId)}`);
    if (!res.ok) {
      return NextResponse.json({ error: 'Book not found' }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch book detail' }, { status: 500 });
  }
}
