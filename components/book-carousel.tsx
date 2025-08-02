"use client"

import { useState } from "react"
import { ChevronLeft, ChevronRight, Star } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import Link from "next/link"

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

interface BookCarouselProps {
  books: Book[]
}

export function BookCarousel({ books }: BookCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0)
  const booksPerView = 6

  const nextSlide = () => {
    setCurrentIndex((prev) => (prev + booksPerView >= books.length ? 0 : prev + booksPerView))
  }

  const prevSlide = () => {
    setCurrentIndex((prev) =>
      prev === 0 ? Math.max(0, books.length - booksPerView) : Math.max(0, prev - booksPerView),
    )
  }

  const visibleBooks = books.slice(currentIndex, currentIndex + booksPerView)

  return (
    <div className="relative">
      <div className="flex items-center space-x-4">
        <Button
          variant="outline"
          size="icon"
          onClick={prevSlide}
          className="shrink-0 rounded-full border-sage-200 hover:bg-sage-50 bg-transparent"
          disabled={currentIndex === 0}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        <div className="flex-1 overflow-hidden">
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {visibleBooks.map((book) => (
              <Link key={book.id} href={`/book/${book.id}`}>
                <Card className="hover:shadow-lg transition-all duration-300 hover:scale-105 cursor-pointer">
                  <CardContent className="p-3">
                    <img
                      src={book.cover || "/placeholder.svg"}
                      alt={book.title}
                      className="w-full h-48 object-cover rounded-md mb-3"
                    />
                    <h4 className="font-semibold text-sm text-sage-800 line-clamp-2 mb-1">{book.title}</h4>
                    <p className="text-xs text-sage-600 mb-2">{book.author}</p>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <Star className="h-3 w-3 text-yellow-400 fill-current" />
                        <span className="text-xs text-sage-600 ml-1">{book.rating}</span>
                      </div>
                      <span className="text-xs text-sage-500">{book.year}</span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>

        <Button
          variant="outline"
          size="icon"
          onClick={nextSlide}
          className="shrink-0 rounded-full border-sage-200 hover:bg-sage-50 bg-transparent"
          disabled={currentIndex + booksPerView >= books.length}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
