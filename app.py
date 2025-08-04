from flask import Flask, request, jsonify
from flask_cors import CORS
from recommender import BookRecommender
import os

app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
BOOKS_CSV = os.path.join(DATA_DIR, "combined_books.csv")
RATINGS_CSV = os.path.join(DATA_DIR, "ratings.csv")
recommender = BookRecommender(BOOKS_CSV, RATINGS_CSV)

@app.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.get_json()
    query = data.get("query", "").strip()
    top_n = int(data.get("top_n", 10))

    # Support special queries for trending, recent, highly rated
    if query.lower() in ["trending", "popular", "most popular"]:
        books = recommender.get_trending_books(top_n=top_n)
        return jsonify({"books": books})
    if query.lower() in ["recent", "recently added", "latest", "new"]:
        books = recommender.get_recent_books(top_n=top_n, min_year=2018)
        return jsonify({"books": books})
    if query.lower() in ["highly rated", "best", "top rated"]:
        books = recommender.get_highly_rated_books(top_n=top_n)
        return jsonify({"books": books})

    results = recommender.mixed_recommendations(query, top_n_api=top_n,top_n_static=top_n)
    if isinstance(results, dict) and "error" in results:
        return jsonify(results), 404
    return jsonify({"books": results})

@app.route("/api/mixed_recommend", methods=["POST"])
def mixed_recommend():
    data = request.get_json()
    query = data.get("query", "")
    top_n_static = int(data.get("top_n_static", 5))
    top_n_api = int(data.get("top_n_api", 5))
    results = recommender.mixed_recommendations(query, top_n_static, top_n_api)
    return jsonify({"books": results})

@app.route("/api/recommend/title", methods=["POST"])
def recommend_by_title():
    data = request.get_json()
    title = data.get("title", "")
    top_n = int(data.get("top_n", 10))
    results = recommender.get_recommendations_by_title(title, top_n=top_n)
    if isinstance(results, dict) and "error" in results:
        return jsonify(results), 404
    return jsonify({"books": results})

@app.route("/api/recommend/genre", methods=["POST"])
def recommend_by_genre():
    data = request.get_json()
    genre = data.get("genre", "")
    top_n = int(data.get("top_n", 10))
    results = recommender.get_recommendations_by_genre(genre, top_n=top_n)
    return jsonify({"books": results})

@app.route("/api/recommend/author", methods=["POST"])
def recommend_by_author():
    data = request.get_json()
    author = data.get("author", "")
    top_n = int(data.get("top_n", 10))
    results = recommender.get_recommendations_by_author(author, top_n=top_n)
    if isinstance(results, dict) and "error" in results:
        return jsonify(results), 404
    return jsonify({"books": results})

@app.route("/api/recommend/keywords", methods=["POST"])
def recommend_by_keywords():
    data = request.get_json()
    keywords = data.get("keywords", [])
    top_n = int(data.get("top_n", 10))
    results = recommender.get_recommendations_by_keywords(keywords, top_n=top_n)
    return jsonify({"books": results})

@app.route("/api/recommend/filters", methods=["POST"])
def recommend_by_filters():
    data = request.get_json()
    genre = data.get("genre")
    year = data.get("year")
    mood_keywords = data.get("mood_keywords")
    top_n = int(data.get("top_n", 10))
    results = recommender.get_recommendations_by_filters(genre, year, mood_keywords, top_n=top_n)
    return jsonify({"books": results})

@app.route('/api/book', methods=['GET'])  # remove trailing '/'
def book_detail():
    
    book_id = request.args.get('book_id')
    print("API called for book_id:", book_id)
    if not book_id:
        return jsonify({'error': 'Missing book_id parameter'}), 400
    result = recommender.get_book_by_id(book_id)
    if result is None:
        return jsonify({'error': 'Book not found'}), 404
    return jsonify(result)

@app.route('/api/similar', methods=['GET'])
def similar_books():
    book_id = request.args.get('book_id')
    if not book_id:
        return jsonify({'books': []})
    results = recommender.similar_books_by_id(book_id, top_n=8)
    return jsonify({'books': results})

@app.route("/")
def health():
    return "Book Recommender API Running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5049,debug=True)

