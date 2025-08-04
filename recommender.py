import pandas as pd
import numpy as np
import ast
import re
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from difflib import get_close_matches
import requests
from collections import Counter

def to_serializable(obj):
        if isinstance(obj, dict):
            return {k: to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, list):
            return [to_serializable(v) for v in obj]
        else:
            return obj
class BookRecommender:
    def __init__(self, books_csv, ratings_csv):
        # Load datasets
        self.df = pd.read_csv(books_csv)
        self.ratings_df = pd.read_csv(ratings_csv)

        # Remove duplicates by original_title
        self.df = self.df.drop_duplicates(subset='original_title', keep='first').reset_index(drop=True)

        # Fill 'Genres' by mode per author if missing
        self.df['Genres'] = self.df.groupby('authors_ratings')['Genres'].transform(
            lambda x: x.fillna(x.mode().iloc[0]) if not x.mode().empty else x
        )

        # Fill Description if missing with "Title by Author"
        def fill_description(row):
            if pd.isna(row['Description']) or not str(row['Description']).strip():
                return f"{row['original_title']} by {row['authors_ratings']}"
            else:
                return row['Description']
        self.df['Description'] = self.df.apply(fill_description, axis=1)

        # Replace missing genres with 'Unknown' safely
        self.df['Genres'] = self.df['Genres'].fillna('Unknown')

        # Fill publication year by mean year grouped by author
        self.df['original_publication_year'] = self.df.groupby('authors_ratings')['original_publication_year'] \
            .transform(lambda x: x.fillna(round(x.mean())) if not x.dropna().empty else x)
        self.df['original_publication_year'] = self.df['original_publication_year'].fillna(0)

        # Ensure Description and Genres are strings
        self.df['Description'] = self.df['Description'].fillna('').astype(str)
        self.df['Genres'] = self.df['Genres'].fillna('').astype(str)

        # Parse genres column from string to list using ast.literal_eval safely
        def safe_parse(val):
            if pd.isna(val):
                return []
            try:
                parsed = ast.literal_eval(val)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                # If parsing fails, fallback to splitting by comma
                if isinstance(val, str):
                    return [g.strip() for g in val.split(",") if g.strip()]
                return []
        self.df['Genres'] = self.df['Genres'].apply(safe_parse)

        # Prepare genre list for smart search routing
        genre_counter = Counter()
        for genres in self.df['Genres']:
            for genre in genres:
                if isinstance(genre, str):
                    genre_counter[genre.strip().lower()] += 1
        self.sorted_genres = sorted(genre_counter.items(), key=lambda x: x[1], reverse=True)
        self.genres_only = [genre.lower() for genre, count in self.sorted_genres]

        # Add a combined content field for TF-IDF
        self.df['combined_content'] = self.df['Description'] + " " + self.df['Genres'].apply(lambda g: ' '.join(g))

        # Content based TF-IDF vectorizer
        self.tfidf = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.tfidf.fit_transform(self.df['combined_content'])

        # Collaborative filtering matrix from ratings
        self.ratings_df = self.ratings_df.rename(columns=lambda x: x.lower())
        book_rating_counts = self.ratings_df['book_id'].value_counts()
        # self.ratings_matrix = self.ratings_df.pivot_table(index='user_id', columns='book_id', values='rating')
        min_ratings = 100 
        popular_books = book_rating_counts[book_rating_counts >= min_ratings].index
        ratings_for_collab = self.ratings_df[self.ratings_df['book_id'].isin(popular_books)]
        self.pivot = ratings_for_collab.pivot_table(index='user_id', columns='book_id', values='rating')
        self.pivot = self.pivot.fillna(0)
        
        # self.ratings_matrix_filled = self.ratings_matrix.fillna(0)
        self.book_id_to_idx = {book_id: idx for idx, book_id in enumerate(self.pivot.columns)}
        self.collaborative_similarity_matrix = cosine_similarity(self.pivot.T)

        # Content similarity matrix
        self.content_similarity_matrix = cosine_similarity(self.tfidf_matrix)

        # Map book_id to index in dataframe
        self.bookid_index = {row['book_id']: idx for idx, row in self.df.iterrows()}

    # Google Books API fetch fallback
    def fetch_books_from_google_api(self, query, max_results=5):
        api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults={max_results*5}"
        try:
            response = requests.get(api_url, timeout=5)
            if response.status_code != 200:
                return []
        except Exception:
            return []
        data = response.json().get('items', [])
        results = []
        for item in data:
            info = item.get('volumeInfo', {})
            ratings_count = info.get('ratingsCount', 0)
            avg_rating = info.get('averageRating', 0)
            results.append({
                'source': 'GoogleBooks',
                'original_title': info.get('title', 'Unknown'),
                'Genres': ', '.join(info.get('categories', ['Unknown'])),
                'original_publication_year': info.get('publishedDate', 'Unknown')[:4],
                'hybrid_score': None,
                'average_rating': avg_rating,
                'ratings_count': ratings_count,
                'description': info.get('description', ''),
                'cover': info.get('imageLinks', {}).get('thumbnail', ''),
                'authors': ', '.join(info.get('authors', [])),
                'pageCount': info.get('pageCount', None),
                'publisher': info.get('publisher', None)
            })
        results = sorted(results, key=lambda x: (x['ratings_count'], x['average_rating']), reverse=True)
        return results[:max_results]

    # Hybrid scorer combining content and collaborative scores plus year recency
    def compute_hybrid_score(self, book_ids, base_idx, top_n=10):
        content_scores = self.content_similarity_matrix[base_idx, book_ids]
        collaborative_scores = self.collaborative_similarity_matrix[base_idx, book_ids] \
            if base_idx < self.collaborative_similarity_matrix.shape[0] else np.zeros(len(book_ids))
        hybrid_scores = 0.3 * content_scores + 0.8 * collaborative_scores

        current_year = self.df['original_publication_year'].max()
        year_scores = 1 - ((current_year - self.df.iloc[book_ids]['original_publication_year']) / 100)
        hybrid_scores += 0.1 * year_scores.clip(lower=0).fillna(0).to_numpy()

        results = self.df.iloc[book_ids].copy()
        results['hybrid_score'] = hybrid_scores
        return results.sort_values(by='hybrid_score', ascending=False).head(top_n)

    # Get trending books (most ratings_count or average_rating)
    def get_trending_books(self, top_n=10):
        df = self.df.copy()
        if 'ratings_count' in df.columns:
            trending = df.sort_values(by=['ratings_count', 'average_rating'], ascending=[False, False]).head(top_n)
        else:
            trending = df.sort_values(by="average_rating", ascending=False).head(top_n)
        return self.df_to_books(trending)

    # Get highly rated books
    def get_highly_rated_books(self, top_n=10):
        df = self.df.copy()
        if 'average_rating' in df.columns:
            rated = df[df['average_rating'] >= 4.3].sort_values(by="average_rating", ascending=False).head(top_n)
        else:
            rated = df.sort_values(by="hybrid_score", ascending=False).head(top_n)
        return self.df_to_books(rated)

    # Get recent books filtered by min_year
    def get_recent_books(self, top_n=10, min_year=None):
        df = self.df.copy()
        if min_year:
            df = df[df['original_publication_year'] >= min_year]
        if df.empty or len(df) < top_n:
            df = self.df.sort_values(by="original_publication_year", ascending=False)
        return self.df_to_books(df.head(top_n))

    # The rest of your recommender methods (title, genre, keywords, author, filters, etc.) remain unchanged, slight style cleanup below.

    def get_recommendations_by_title(self, title, top_n=10):
        title_lower = title.lower()
        titles_in_data = self.df['original_title'].dropna().str.lower().tolist()
        if title_lower not in titles_in_data:
            close_titles = get_close_matches(title, self.df['original_title'].dropna().tolist(), n=3, cutoff=0.6)
            return {"error": f"Book not found. Did you mean: {', '.join(close_titles)}?"}
        base_idx = self.df[self.df['original_title'].str.lower() == title_lower].index[0]
        sim_scores = self.content_similarity_matrix[base_idx]
        top_ids = sim_scores.argsort()[-top_n - 20:][::-1]
        dfout = self.compute_hybrid_score(top_ids, base_idx, top_n)
        return self.df_to_books(dfout)

    def get_recommendations_by_genre(self, genre, top_n=10):
        mask = self.df['Genres'].apply(lambda glist: any(genre.lower() in g.lower() for g in glist if isinstance(g, str)))
        filtered = self.df[mask]
        if filtered.empty:
            api_results = self.fetch_books_from_google_api(genre, top_n)
            return self.api_results_to_books(api_results, top_n)
        base_idx = filtered.index[0]
        dfout = self.compute_hybrid_score(filtered.index.tolist(), base_idx, top_n)
        return self.df_to_books(dfout)

    def get_recommendations_by_keywords(self, keywords, top_n=10):
        if isinstance(keywords, list):
            query = ' '.join(keywords)
        else:
            query = keywords
        query_vec = self.tfidf.transform([query])
        sim_scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_ids = sim_scores.argsort()[-top_n - 20:][::-1]
        base_idx = top_ids[0]
        dfout = self.compute_hybrid_score(top_ids, base_idx, top_n)
        return self.df_to_books(dfout)

    def get_recommendations_by_filters(self, genre=None, year=None, mood_keywords=None, top_n=10):
        df_filtered = self.df.copy()
        if genre:
            df_filtered = df_filtered[
                df_filtered['Genres'].apply(lambda glist: any(genre.lower() in g.lower() for g in glist if isinstance(g, str)))
            ]
        if year:
            df_filtered = df_filtered[df_filtered['original_publication_year'] >= float(year)]
        if mood_keywords:
            if isinstance(mood_keywords, list):
                query = ' '.join(mood_keywords)
            else:
                query = mood_keywords
            query_vec = self.tfidf.transform([query])
            sim_scores = cosine_similarity(query_vec, self.tfidf.transform(df_filtered['combined_content'])).flatten()
            df_filtered = df_filtered.assign(keyword_score=sim_scores)
            df_filtered = df_filtered[df_filtered['keyword_score'] > 0]
        if df_filtered.empty:
            api_results = self.fetch_books_from_google_api(genre if genre else ' '.join(mood_keywords or []), top_n)
            return self.api_results_to_books(api_results, top_n)
        base_idx = df_filtered.index[0]
        dfout = self.compute_hybrid_score(df_filtered.index.tolist(), base_idx, top_n)
        return self.df_to_books(dfout)

    def get_recommendations_by_author(self, author_name, top_n=10):
        mask = self.df['authors_ratings'].str.lower().str.contains(author_name.lower(), na=False)
        matched_books = self.df[mask]
        if matched_books.empty:
            all_authors = self.df['authors_ratings'].dropna().unique().tolist()
            close_matches = get_close_matches(author_name, all_authors, n=3, cutoff=0.6)
            return {"error": f"Author not found. Did you mean: {', '.join(close_matches)}?" if close_matches else "Author not found."}
        dfout = matched_books.copy()
        if 'hybrid_score' in dfout.columns:
            dfout = dfout.sort_values(by='hybrid_score', ascending=False)
        return self.df_to_books(dfout.head(top_n))
    

    def get_book_by_id(self, book_id):
        book_id_int = int(book_id)
        row = self.df[self.df['book_id'] == book_id_int]
        if row.empty:
            return None
        
        book_dict = self.row_to_book(row.iloc[0])
        return to_serializable(book_dict)

    def similar_books_by_id(self, book_id, top_n=8):
        book_id_int = int(book_id)
        if book_id_int not in self.bookid_index:
            return []
        base_idx = self.bookid_index[book_id_int]
        qvec = self.tfidf.transform([self.df.iloc[base_idx]['combined_content']])
        sims = cosine_similarity(qvec, self.tfidf_matrix).flatten()
        sims[base_idx] = -1
        idxs = np.argpartition(-sims, range(top_n * 2))[:top_n * 2]
        candidates = self.df.iloc[idxs]
        candidates = candidates[candidates['book_id'] != book_id_int]
        if len(candidates) < top_n:
            genres = self.df.iloc[base_idx]['Genres']
            by_genre = self.df[self.df['Genres'].apply(lambda glist: any(x in glist for x in genres))]
            by_author = self.df[self.df['authors_ratings'] == self.df.iloc[base_idx]['authors_ratings']]
            fallback = pd.concat([by_genre, by_author]).drop_duplicates()
            fallback = fallback[fallback['book_id'] != book_id_int]
            candidates = pd.concat([candidates, fallback]).drop_duplicates().head(top_n)
        books = self.df_to_books(candidates.head(top_n))   # list of dicts
    # NEW: make each book dict serializable
        return [to_serializable(book) for book in books]

    def smart_route_query(self, query: str, top_n=10):
        query_lower = query.lower().strip()
        if query_lower in ['trending', 'popular', 'most popular']:
            return self.get_trending_books(top_n=top_n)
        if query_lower in ['recent', 'recently added', 'latest', 'new']:
            return self.get_recent_books(top_n=top_n, min_year=2018)
        if query_lower in ['highly rated', 'best', 'top rated']:
            return self.get_highly_rated_books(top_n=top_n)

        titles_lower = self.df['original_title'].dropna().str.lower().tolist()
        if query_lower in titles_lower:
            return self.get_recommendations_by_title(query, top_n)

        matched_genres = [g for g in self.genres_only if g in query_lower]
        if matched_genres:
            return self.get_recommendations_by_genre(matched_genres[0], top_n)

        authors_lower = self.df['authors_ratings'].dropna().str.lower().tolist()
        possible_authors = [a for a in authors_lower if query_lower in a]
        if possible_authors:
            return self.get_recommendations_by_author(possible_authors[0], top_n)

        return self.get_recommendations_by_keywords(query, top_n)
    
    def mixed_recommendations(self, query, top_n_static=5, top_n_api=5):
    # Get from local ML
        static_df = pd.DataFrame(self.smart_route_query(query, top_n=top_n_static + 5))
        if static_df.empty:
            combined_static = pd.DataFrame()
        else:
            top_2 = static_df.head(2)
            rest = static_df.iloc[2:]
            if len(rest) > 0:
                rest_sorted = rest.sort_values(by='year', ascending=False).head(top_n_static - 2)
            else:
                rest_sorted = pd.DataFrame()
        combined_static = pd.concat([top_2, rest_sorted], ignore_index=True)
        combined_static['source'] = 'Local'

    # Now fetch from API
        api_results = self.fetch_books_from_google_api(query, max_results=top_n_api)
        api_df = pd.DataFrame(api_results)
        if not api_df.empty:
            api_df['source'] = 'GoogleBooks'

    # Combine both
        final_df = pd.concat([combined_static, api_df], ignore_index=True)
    # Fill missing columns for harmony
        needed_cols = ['source', 'title', 'genres', 'year', 'rating', 'cover', 'description']
        for col in needed_cols:
            if col not in final_df.columns:
                final_df[col] = None
        return final_df[needed_cols].to_dict(orient='records')


    def df_to_books(self, df):
        out = []
        for _, row in df.iterrows():
            out.append(self.row_to_book(row))
        return out

    def api_results_to_books(self, api_results, top_n=10):
        out = []
        for entry in api_results[:top_n]:
            out.append({
                "id": None,
                "title": entry.get('original_title'),
                "author": entry.get('authors'),
                "genres": [g.strip() for g in entry.get('Genres', '').split(',') if g.strip()],
                "year": entry.get('original_publication_year', None),
                "rating": entry.get('average_rating', None),
                "cover": entry.get('cover', ''),
                "description": entry.get('description', ''),
                "publisher": entry.get('publisher', None),
                "pages": entry.get('pageCount', None),
                "source": entry.get('source', 'GoogleBooks')
            })
        return out

    def row_to_book(self, row):
        out = {
            "id": row["book_id"] if "book_id" in row else None,
            "title": row["original_title"],
            "author": row["authors_ratings"],
            "genres": [g.strip() for g in row["Genres"] if isinstance(g, str)],
            "year": int(row["original_publication_year"]) if pd.notna(row["original_publication_year"]) else None,
            "publisher": row.get('publisher', None) if 'publisher' in row else None,
            "pages": row.get('num_pages', None) if 'num_pages' in row else None,
            "cover": row.get('Image-URL-L', ""),
            "description": row.get('Description', ""),
            "rating": float(row["average_rating"]) if 'average_rating' in row and pd.notna(row["average_rating"]) else None,
            "source": "Local"
        }

        # Enrich missing data via Google Books API if needed
        if (not out["cover"] or not out["description"]) and out["title"] and out["author"]:
            gbooks = self.fetch_books_from_google_api(f'{out["title"]} {out["author"]}', max_results=1)
            if gbooks and len(gbooks) > 0:
                g = gbooks[0]
                out["cover"] = out["cover"] or g.get('cover')
                out["description"] = out["description"] or g.get('description')
                out["publisher"] = out["publisher"] or g.get('publisher')
                out["pages"] = out["pages"] or g.get('pageCount')
                out["year"] = out["year"] or (g.get('original_publication_year', '')[:4] if g.get('original_publication_year') else None)

        return out
