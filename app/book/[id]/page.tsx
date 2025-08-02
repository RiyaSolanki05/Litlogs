"use client"

import { useState, useEffect } from "react"
import { Search, MessageCircle, BookOpen, Star, TrendingUp, Users, Clock, Award } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import Link from "next/link"
import Image from "next/image"
import { ChatBot } from "@/components/chat-bot"
import { BookCarousel } from "@/components/book-carousel"

interface Book {
  id: string
  title: string
  author: string
  genres: string[]
  year: number
  rating: number
  cover: string
  description: string
}

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [searchResults, setSearchResults] = useState<Book[]>([])
  const [isSearching, setIsSearching] = useState(false)

  const [trendingBooks, setTrendingBooks] = useState<Book[]>([])
  const [mysteryBooks, setMysteryBooks] = useState<Book[]>([])
  const [scifiBooks, setSciFiBooks] = useState<Book[]>([])
  const [romanceBooks, setRomanceBooks] = useState<Book[]>([])
  const [recentBooks, setRecentBooks] = useState<Book[]>([])
  const [highRatedBooks, setHighRatedBooks] = useState<Book[]>([])

  // Search handler with debouncing
  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([])
      return
    }
    setIsSearching(true)
    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`)
      const data = await response.json()
      setSearchResults(data.books || [])
    } catch (error) {
      console.error("Search error:", error)
      setSearchResults([])
    } finally {
      setIsSearching(false)
    }
  }

  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      handleSearch(searchQuery)
    }, 300)
    return () => clearTimeout(debounceTimer)
  }, [searchQuery])

  // Load carousel data from backend on mount
  useEffect(() => {
    // Fetch Trending Now
    fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: "trending", top_n: 30 }),
    })
      .then(res => res.json())
      .then(data => setTrendingBooks(data.books ?? []))
      .catch(() => setTrendingBooks([]))

    // Fetch Mystery & Thriller
    fetch("/api/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: "genre", query: "Mystery", limit: 30 }),
    })
      .then(res => res.json())
      .then(data => setMysteryBooks(data.recommendations ?? []))
      .catch(() => setMysteryBooks([]))

    // Fetch Science Fiction
    fetch("/api/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: "genre", query: "Science Fiction", limit: 30 }),
    })
      .then(res => res.json())
      .then(data => setSciFiBooks(data.recommendations ?? []))
      .catch(() => setSciFiBooks([]))

    // Fetch Romance
    fetch("/api/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: "genre", query: "Romance", limit: 30 }),
    })
      .then(res => res.json())
      .then(data => setRomanceBooks(data.recommendations ?? []))
      .catch(() => setRomanceBooks([]))

    // Fetch Recently Added (books published after 2018)
    fetch("/api/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "filters",
        query: "",
        filters: { year: 2000 },
        limit: 30,
      }),
    })
      .then(res => res.json())
      .then(data => setRecentBooks(data.recommendations ?? []))
      .catch(() => setRecentBooks([]))

    // Fetch Highly Rated
    fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: "highly rated", top_n: 12 }),
    })
      .then(res => res.json())
      .then(data => setHighRatedBooks(data.books ?? []))
      .catch(() => setHighRatedBooks([]))
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-sage-50 to-sage-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-sage-200 sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-3">
              <Image src="/logo.png" alt="Litlogs" width={50} height={50} className="rounded-full" />
              <h1 className="text-2xl font-bold text-sage-800">Litlogs</h1>
            </Link>
            <div className="flex-1 max-w-2xl mx-8">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-sage-400 h-5 w-5" />
                <Input
                  type="text"
                  placeholder="Search for books, authors, or genres..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-3 w-full border-sage-200 focus:border-sage-400 focus:ring-sage-400 rounded-full"
                />
              </div>
            </div>
            <Button
              onClick={() => setIsChatOpen(true)}
              className="bg-sage-600 hover:bg-sage-700 text-white rounded-full p-3"
            >
              <MessageCircle className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </header>

      {/* Search Results */}
      {searchQuery && (
        <div className="container mx-auto px-4 py-6">
          <h2 className="text-2xl font-bold text-sage-800 mb-4">Search Results for "{searchQuery}"</h2>
          {isSearching ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sage-600 mx-auto" />
              <p className="text-sage-600 mt-2">Searching...</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {searchResults.map((book) => (
                <Link key={book.id} href={`/book/${book.id}`}>
                  <Card className="hover:shadow-lg transition-shadow cursor-pointer">
                    <CardContent className="p-3">
                      <img
                        src={book.cover || "/placeholder.svg"}
                        alt={book.title}
                        className="w-full h-48 object-cover rounded-md mb-2"
                      />
                      <h3 className="font-semibold text-sm text-sage-800 line-clamp-2">{book.title}</h3>
                      <p className="text-xs text-sage-600 mt-1">{book.author}</p>
                      <div className="flex items-center mt-2">
                        <Star className="h-3 w-3 text-yellow-400 fill-current" />
                        <span className="text-xs text-sage-600 ml-1">{book.rating}</span>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Main Content - Genre Carousels */}
      {!searchQuery && (
        <main className="container mx-auto px-4 py-8">
          {/* Hero Section */}
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-sage-800 mb-4">Discover Your Next Great Read</h2>
            <p className="text-lg text-sage-600 max-w-2xl mx-auto">
              Explore personalized book recommendations powered by advanced machine learning
            </p>
          </div>

          {/* Genre Carousels */}
          <div className="space-y-12">
            <div>
              <div className="flex items-center mb-6">
                <TrendingUp className="h-6 w-6 text-sage-600 mr-3" />
                <h3 className="text-2xl font-bold text-sage-800">Trending Now</h3>
              </div>
              <BookCarousel books={trendingBooks} />
            </div>
            <div>
              <div className="flex items-center mb-6">
                <BookOpen className="h-6 w-6 text-sage-600 mr-3" />
                <h3 className="text-2xl font-bold text-sage-800">Mystery & Thriller</h3>
              </div>
              <BookCarousel books={mysteryBooks} />
            </div>
            <div>
              <div className="flex items-center mb-6">
                <Star className="h-6 w-6 text-sage-600 mr-3" />
                <h3 className="text-2xl font-bold text-sage-800">Science Fiction</h3>
              </div>
              <BookCarousel books={scifiBooks} />
            </div>
            <div>
              <div className="flex items-center mb-6">
                <Users className="h-6 w-6 text-sage-600 mr-3" />
                <h3 className="text-2xl font-bold text-sage-800">Romance</h3>
              </div>
              <BookCarousel books={romanceBooks} />
            </div>
            <div>
              <div className="flex items-center mb-6">
                <Clock className="h-6 w-6 text-sage-600 mr-3" />
                <h3 className="text-2xl font-bold text-sage-800">Recently Added</h3>
              </div>
              <BookCarousel books={recentBooks} />
            </div>
            <div>
              <div className="flex items-center mb-6">
                <Award className="h-6 w-6 text-sage-600 mr-3" />
                <h3 className="text-2xl font-bold text-sage-800">Highly Rated</h3>
              </div>
              <BookCarousel books={highRatedBooks} />
            </div>
          </div>
        </main>
      )}

      {/* Chatbot */}
      <ChatBot isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </div>
  )
}
