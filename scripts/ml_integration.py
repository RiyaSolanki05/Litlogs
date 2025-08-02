#!/usr/bin/env python3
"""
Book Recommendation ML Integration Script
Adapted from the provided hybrid_book_recommender.py
"""

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from difflib import get_close_matches
import requests
import json
import sys

class BookRecommendationSystem:
    def __init__(self, books_csv_path, ratings_csv_path):
        """Initialize the recommendation system with data paths"""
        self.df = pd.read_csv(books_csv_path)
        self.ratings_df = pd.read_csv(ratings_csv_path)
        self.setup_data()
        self.setup_models()
    
    def setup_data(self):
        """Preprocess the data"""
        # Remove duplicates and handle missing values
        self.df = self.df.drop_duplicates(subset='original_title', keep='first').reset_index(drop=True)
        
        # Fill missing genres
        self.df['Genres'] = self.df.groupby('authors_ratings')['Genres'].transform(
            lambda x: x.fillna(x.mode().iloc[0]) if not x.mode().empty else x
        )
        
        # Fill missing descriptions
        self.df['Description'] = self.df.apply(
            lambda row: f"{row['original_title']} by {row['authors_ratings']}" 
            if pd.isna(row['Description']) or not row['Description'].strip() 
            else row['Description'], axis=1
        )
        
        # Fill remaining missing values
        self.df['Genres'].fillna('Unknown', inplace=True)
        self.df['original_publication_year'] = self.df.groupby('authors_ratings')['original_publication_year'].transform(
            lambda x: x.fillna(round(x.mean())) if not x.dropna().empty else x
        )
        self.df['original_publication_year'] = self.df['original_publication_year'].fillna(0)
        self.df['Description'] = self.df['Description'].fillna('').astype(str)
        self.df['Genres'] = self.df['Genres'].fillna('').astype(str)
        self.df['combined_content'] = self.df['Description'] + " " + self.df['Genres']
    
    def setup_models(self):
        """Setup similarity matrices"""
        # Ratings matrix for collaborative filtering
        ratings_matrix = self.ratings_df.pivot_table(index='user_id', columns='book_id', values='rating')
        ratings_matrix_filled = ratings_matrix.fillna(0)
        self.book_id_to_idx = {book_id: idx for idx, book_id in enumerate(ratings_matrix.columns)}
        self.collaborative_similarity_matrix = cosine_similarity(ratings_matrix_filled.T)
        
        # Content-based filtering
        self.tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = self.tfidf.fit_transform(self.df['combined_content'])
        self.content_similarity_matrix = cosine_similarity(tfidf_matrix)
    
    def compute_hybrid_score(self, book_ids, base_idx, top_n=10):
        """Compute hybrid recommendation scores"""
        content_scores = self.content_similarity_matrix[base_idx, book_ids]
        collaborative_scores = (
            self.collaborative_similarity_matrix[base_idx, book_ids] 
            if base_idx < self.collaborative_similarity_matrix.shape[0] 
            else np.zeros(len(book_ids))
        )
        
        hybrid_scores = 0.3 * content_scores + 0.8 * collaborative_scores
        
        # Add recency bonus
        current_year = self.df['original_publication_year'].max()
        year_scores = 1 - ((current_year - self.df.iloc[book_ids]['original_publication_year']) / 100)
        hybrid_scores += 0.1 * year_scores.clip(lower=0).fillna(0).to_numpy()
        
        results = self.df.iloc[book_ids].copy()
        results['hybrid_score'] = hybrid_scores
        
        return results[['book_id', 'original_title', 'Genres', 'original_publication_year', 'hybrid_score']].sort_values(
            by='hybrid_score', ascending=False
        ).head(top_n)
    
    def get_recommendations_by_title(self, title, top_n=10):
        """Get recommendations based on book title"""
        if title.lower() not in self.df['original_title'].str.lower().values:
            close_titles = get_close_matches(title, self.df['original_title'].dropna().tolist(), n=3, cutoff=0.6)
            return {"error": f"Book not found. Did you mean: {', '.join(close_titles)}?"}
        
        base_idx = self.df[self.df['original_title'].str.lower() == title.lower()].index[0]
        sim_scores = self.content_similarity_matrix[base_idx]
        top_ids = sim_scores.argsort()[-top_n-20:][::-1]
        
        return self.compute_hybrid_score(top_ids, base_idx, top_n).to_dict('records')
    
    def get_recommendations_by_genre(self, genre, top_n=10):
        """Get recommendations based on genre"""
        filtered_books = self.df[self.df['Genres'].str.contains(genre, case=False, na=False)]
        if filtered_books.empty:
            return []
        
        base_idx = filtered_books.index[0]
        return self.compute_hybrid_score(filtered_books.index.tolist(), base_idx, top_n).to_dict('records')
    
    def get_recommendations_by_author(self, author_name, top_n=10):
        """Get recommendations based on author"""
        matched_books = self.df[self.df['authors_ratings'].str.lower().str.contains(author_name.lower(), na=False)]
        
        if matched_books.empty:
            all_authors = self.df['authors_ratings'].dropna().unique().tolist()
            close_matches = get_close_matches(author_name, all_authors, n=3, cutoff=0.6)
            return {"error": f"Author not found. Did you mean: {', '.join(close_matches)}?" if close_matches else "Author not found."}
        
        return matched_books[['original_title', 'authors_ratings', 'Genres', 'original_publication_year']].head(top_n).to_dict('records')
    
    def get_recommendations_by_keywords(self, keywords, top_n=10):
        """Get recommendations based on keywords"""
        query = ' '.join(keywords) if isinstance(keywords, list) else keywords
        query_vec = self.tfidf.transform([query])
        sim_scores = cosine_similarity(query_vec, self.tfidf.transform(self.df['combined_content'])).flatten()
        top_ids = sim_scores.argsort()[-top_n-20:][::-1]
        base_idx = top_ids[0]
        
        return self.compute_hybrid_score(top_ids, base_idx, top_n).to_dict('records')
    
    def smart_route_query(self, query, top_n=10):
        """Smart query routing based on content"""
        query_lower = query.strip().lower()
        
        # Check if it's a title
        titles_lower = self.df['original_title'].dropna().str.lower().tolist()
        if query_lower in titles_lower:
            return self.get_recommendations_by_title(query, top_n=top_n)
        
        # Check for genre keywords
        genres = ["fantasy", "romance", "thriller", "science fiction", "horror", "mystery", "historical"]
        matched_genres = [g for g in genres if g in query_lower]
        if matched_genres:
            return self.get_recommendations_by_genre(matched_genres[0], top_n=top_n)
        
        # Check for author
        authors_lower = self.df['authors_ratings'].dropna().str.lower().tolist()
        possible_authors = [a for a in authors_lower if query_lower in a]
        if possible_authors:
            return self.get_recommendations_by_author(possible_authors[0], top_n=top_n)
        
        # Fallback to keyword search
        return self.get_recommendations_by_keywords(query, top_n=top_n)

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 4:
        print("Usage: python ml_integration.py <books_csv> <ratings_csv> <query>")
        sys.exit(1)
    
    books_csv = sys.argv[1]
    ratings_csv = sys.argv[2]
    query = sys.argv[3]
    
    # Initialize recommendation system
    recommender = BookRecommendationSystem(books_csv, ratings_csv)
    
    # Get recommendations
    results = recommender.smart_route_query(query, top_n=10)
    
    # Output as JSON
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
