<img src="./public/logo.png" alt="Litlogs Logo" width="100" height="100" />  
LITLOGS - Intelligent Book Recommendation System

A modern, user-friendly book recommendation web application built with a Next.js React frontend and a powerful Flask-based machine learning backend. Litlogs provides personalized, genre-based, and hybrid recommendations by leveraging a large dataset of over 9,000 books and nearly 6 million user ratings.

🚀 Key Features
**Advanced Hybrid Recommendations**
Combines collaborative filtering with content-based methods (TF-IDF, cosine similarity, fuzzy search) to suggest books users will love.

**Diverse Search Options**
Search by title, author, genre, keywords, or with custom filters (year, mood).

**Dynamic Carousels**
Netflix-style sliding book rows on homepage — Trending, Recently Added, Highly Rated, Mystery, Sci-Fi, Romance, and more.

**Detailed Book Pages**
View comprehensive book info: description, ratings, year, genres, author info, publication details, pages, cover images.

**Google Books API Enrichment**
Automatically fills missing metadata (covers, descriptions, etc.) by fetching real-time data from Google Books.

**Fast & Scalable**
Backend loads and preprocesses all data once at startup, serving queries quickly.

📊 Dataset
Books: **~9,000 titles** with metadata including genres, authors, descriptions, publication years, and cover URLs.

Ratings: Nearly **6 million user-generated ratings** providing rich collaborative signal.

Origin of datasets: **Publicly available book datasets **(e.g., from Goodreads or similar sources).

🛠️ Technology Stack
Layer	Technology
Frontend	Next.js 13, React, TypeScript, Tailwind CSS
Backend	Python 3.9+, Flask, Pandas, scikit-learn, NumPy, Requests
ML Recommender	Hybrid ML model: content-based (TF-IDF, cosine similarity), collaborative filtering, fuzzy text matching
APIs	Internal API routing with Next.js serverless routes (proxies to Flask backend)


🔍 How It Works
Frontend UI lets users browse categorized book carousels and perform searches.

Calls are routed to backend API endpoints for recommendations and book details.

The Flask backend loads datasets once, preprocesses, and performs hybrid ML recommendations.

Backend augments incomplete data from Google Books API as needed.

Results stream back to the frontend reactively and are displayed dynamically in the UI.

✨ Highlights & Benefits
Combines best of content similarity and user rating data.

Interactive and intuitive UX inspired by Netflix-style browsing.

Handles millions of ratings efficiently with scalable Python ML.

Real-time metadata enrichment with external APIs.

Easily customizable backend or frontend to add more features.
