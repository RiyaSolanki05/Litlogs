"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";;
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowLeft, Star, Calendar, BookOpen, Users, Heart, Share2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import Link from "next/link"
import Image from "next/image"
import { BookCarousel } from "@/components/book-carousel"

interface BookDetails {
  id: string;
  title: string;
  author: string;
  genres: string[];
  year: number;
  rating: number;
  ratings_count: number;
  pages: number;
  cover: string;
  description: string;
  isbn?: string;
  publisher?: string;
  language?: string;
}

export default function BookDetailPage() {
  const params = useParams();
  const router = useRouter();

  const [book, setBook] = useState<BookDetails | null>(null);
  const [similarBooks, setSimilarBooks] = useState<BookDetails[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isFavorited, setIsFavorited] = useState(false)
  console.log("Navigating to book_id:", params.id);
  useEffect(() => {
    async function fetchBookAndSimilar() {
      setIsLoading(true);
      try {
        // Fetch main book details
        const res = await fetch(`/api/book?book_id=${encodeURIComponent(params.id as string)}`);
        if (!res.ok) {
          setBook(null);
          setSimilarBooks([]);
        } else {
          const data = await res.json();
          setBook({
            id: data.id || data.book_id,
            title: data.title || data.original_title,
            author: data.author || data.authors || data.authors_ratings,
            genres: data.genres || data.Genres || [],
            year: data.year || data.original_publication_year,
            rating: data.rating || data.average_rating,
            ratings_count: data.ratings_count || data.ratingsCount || 0,
            pages: data.pages || data.num_pages || 0,
            cover: data.cover || data["Image-URL-L"] || "/placeholder.svg",
            description: data.description || data.Description || "",
            isbn: data.isbn13,
            publisher: data.publisher,
            language: data.language,
          });

          // Fetch similar books
          const simRes = await fetch(`/api/similar/?book_id=${encodeURIComponent(params.id as string)}`);
          if (simRes.ok) {
            const simData = await simRes.json();
            setSimilarBooks(simData.books || []);
          } else {
            setSimilarBooks([]);
          }
        }
      } catch {
        setBook(null);
        setSimilarBooks([]);
      } finally {
        setIsLoading(false);
      }
    }

    if (params.id) fetchBookAndSimilar();
  }, [params.id]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sage-50 to-sage-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-600"></div>
      </div>
    )
  }

  if (!book) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sage-50 to-sage-100 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-sage-800 mb-4">Book Not Found</h1>
          <Button onClick={() => router.back()} className="bg-sage-600 hover:bg-sage-700">
            Go Back
          </Button>
        </div>
      </div>
    )
  }

  return (
        <div className="min-h-screen bg-gradient-to-br from-sage-50 to-sage-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-sage-200 sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="icon" onClick={() => router.back()} className="rounded-full">
                <ArrowLeft className="h-5 w-5" />
              </Button>
              <Link href="/" className="flex items-center space-x-3">
                <Image src="/logo.png" alt="Litlogs" width={40} height={40} className="rounded-full" />
                <h1 className="text-xl font-bold text-sage-800">Litlogs</h1>
              </Link>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="icon"
                onClick={() => setIsFavorited(!isFavorited)}
                className={`rounded-full ${isFavorited ? "bg-red-50 border-red-200" : ""}`}
              >
                <Heart className={`h-5 w-5 ${isFavorited ? "text-red-500 fill-current" : "text-sage-600"}`} />
              </Button>
              <Button variant="outline" size="icon" className="rounded-full bg-transparent">
                <Share2 className="h-5 w-5 text-sage-600" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Book Details */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
          {/* Book Cover */}
          <div className="lg:col-span-1">
            <Card className="overflow-hidden">
              <CardContent className="p-0">
                <img src={book.cover || "/placeholder.svg"} alt={book.title} className="w-full h-auto object-cover" />
              </CardContent>
            </Card>
          </div>

          {/* Book Information */}
          <div className="lg:col-span-2 space-y-6">
            <div>
              <h1 className="text-4xl font-bold text-sage-800 mb-2">{book.title}</h1>
              <p className="text-xl text-sage-600 mb-4">by {book.author}</p>

              <div className="flex flex-wrap gap-2 mb-4">
                {book.genres.map((genre) => (
                  <Badge key={genre} variant="secondary" className="bg-sage-100 text-sage-700">
                    {genre}
                  </Badge>
                ))}
              </div>

              <div className="flex items-center space-x-6 text-sage-600">
                <div className="flex items-center space-x-2">
                  <Star className="h-5 w-5 text-yellow-400 fill-current" />
                  <span className="font-semibold">{book.rating}</span>
                  <span>({book.ratings_count.toLocaleString()} ratings)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Calendar className="h-5 w-5" />
                  <span>{book.year}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <BookOpen className="h-5 w-5" />
                  <span>{book.pages} pages</span>
                </div>
              </div>
            </div>

            <Separator />

            <div>
              <h2 className="text-2xl font-bold text-sage-800 mb-4">Description</h2>
              <p className="text-sage-700 leading-relaxed">{book.description}</p>
            </div>

            <Separator />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg text-sage-800">Publication Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sage-600">Publisher:</span>
                    <span className="text-sage-800">{book.publisher}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sage-600">ISBN:</span>
                    <span className="text-sage-800">{book.isbn}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sage-600">Language:</span>
                    <span className="text-sage-800">{book.language}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg text-sage-800">Reader Stats</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sage-600">Average Rating:</span>
                    <span className="text-sage-800">{book.rating}/5</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sage-600">Total Ratings:</span>
                    <span className="text-sage-800">{book.ratings_count.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sage-600">Pages:</span>
                    <span className="text-sage-800">{book.pages}</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>

      <div className="mt-8">
        <h2 className="text-2xl font-bold text-sage-800">Similar Books</h2>
        {similarBooks.length === 0 ? (
          <p>No similar books found.</p>
        ) : (
          <ul className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {similarBooks.map((simBook) => (
              <li key={simBook.id} className="border rounded p-2 hover:shadow">
                <Link href={`/book/${simBook.id}`}>
                  <Image
                    src={simBook.cover || "/placeholder.svg"}
                    alt={simBook.title}
                    width={120}
                    height={180}
                    className="rounded"
                  />
                  <p className="mt-2 font-semibold">{simBook.title}</p>
                  <p className="text-sm text-muted-foreground">
                    by {simBook.author}
                  </p>
                  <p className="text-sm">
                    ⭐ {simBook.rating ? simBook.rating.toFixed(1) : "?"}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
      </main>
    </div>
  );
}
