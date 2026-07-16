# ?? CineMatch — Fully Offline Movie Recommender System

> A Netflix-inspired movie recommendation engine powered entirely by **TF-IDF + Cosine Similarity**. No internet, no API keys, no TMDB — just your local data files.

---

## ?? Table of Contents

- [Quick Start — How to Run](#-quick-start--how-to-run)
- [Tech Stack](#-tech-stack)
- [Architecture Overview](#-architecture-overview)
- [Project Structure](#-project-structure)
- [Data Architecture](#-data-architecture)
- [How the Recommender Works](#-how-the-recommender-works)
- [API Endpoints](#-api-endpoints)
- [Frontend Features](#-frontend-features)
- [Troubleshooting](#-troubleshooting)

---

## ?? Quick Start — How to Run

You need **two terminals** open at the same time — one for the backend API, one for the frontend UI.

### Step 1 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2 — Start the Backend (FastAPI)

Open **Terminal 1** and run:

```bash
python -m uvicorn main:app --reload
```

? You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
[OK] Loaded 45447 movies, 42227 indexed titles, TF-IDF matrix shape: (45447, 50000)
```

> The `--reload` flag auto-restarts the server when you edit `main.py`. Remove it in production.

### Step 3 — Start the Frontend (Streamlit)

Open **Terminal 2** and run:

```bash
streamlit run app.py
```

? You should see:
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

### Step 4 — Open in Browser

Go to ? **http://localhost:8501**

> The FastAPI interactive docs (Swagger UI) are also available at ? **http://127.0.0.1:8000/docs**

---

## ?? Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | FastAPI | REST API server |
| **ASGI Server** | Uvicorn | Runs the FastAPI app |
| **ML / Recommendation** | scikit-learn | TF-IDF vectorizer (for unpickling) |
| **Data Processing** | Pandas + NumPy | DataFrame ops, matrix math |
| **Sparse Matrix Math** | SciPy | Efficient cosine similarity |
| **Frontend** | Streamlit | Interactive web UI |
| **HTTP Client** | Requests | Streamlit ? FastAPI calls |
| **Data Format** | Pickle + CSV | Serialized ML objects + metadata |
| **Styling** | Vanilla CSS (injected via Streamlit) | Netflix dark theme |
| **Fonts** | Google Fonts — Inter | Modern typography |

---

## ?? Architecture Overview

```
+-----------------------------------------------------------+
¦                     User's Browser                         ¦
¦                  http://localhost:8501                      ¦
+-----------------------------------------------------------+
                      ¦  Streamlit renders HTML/CSS
                      ?
+-----------------------------------------------------------+
¦               Streamlit Frontend (app.py)                   ¦
¦                                                             ¦
¦  • Netflix dark theme (#0a0a0a + #e50914 red accent)       ¦
¦  • Sidebar: Genre / Language / Year / Sort filters         ¦
¦  • Search bar with live autocomplete dropdown              ¦
¦  • 4-column responsive movie card grid                     ¦
¦  • Detail view with similarity progress bars               ¦
+-----------------------------------------------------------+
                      ¦  HTTP GET (localhost only)
                      ?
+-----------------------------------------------------------+
¦               FastAPI Backend (main.py)                     ¦
¦               http://127.0.0.1:8000                         ¦
¦                                                             ¦
¦  GET /home        ? filtered + sorted movie list           ¦
¦  GET /search      ? partial title search (up to 20)        ¦
¦  GET /movie/{t}   ? full movie details                     ¦
¦  GET /recommend   ? TF-IDF top-10 similar movies           ¦
¦  GET /genres      ? unique genre list for sidebar          ¦
¦  GET /languages   ? unique language codes for sidebar      ¦
+-----------------------------------------------------------+
                      ¦  Loaded once at startup
                      ?
+-----------------------------------------------------------+
¦                   Local Data Files (offline)                ¦
¦                                                             ¦
¦  df.pkl            ? 45,447-row movie DataFrame            ¦
¦  indices.pkl       ? title ? matrix row index map          ¦
¦  tfidf_matrix.pkl  ? (45447 × 50000) sparse TF-IDF matrix  ¦
¦  tfidf.pkl         ? fitted TfidfVectorizer object         ¦
¦  movies_metadata.csv ? 24-column raw metadata CSV          ¦
+-----------------------------------------------------------+
```

---

## ?? Project Structure

```
Movie_Recommender_system/
¦
+-- main.py                         # FastAPI backend — all API logic
+-- app.py                          # Streamlit frontend — Netflix UI
+-- requirements.txt                # Python dependencies
+-- README.md                       # This file
¦
+-- df.pkl                          # Core DataFrame (45,447 movies)
+-- indices.pkl                     # Title ? row-index mapping
+-- tfidf_matrix.pkl                # Pre-trained TF-IDF sparse matrix
+-- tfidf.pkl                       # Fitted TfidfVectorizer
¦
+-- movies_metadata.csv             # Full 24-column TMDB metadata
¦
+-- Movie_Recommender_System.ipynb  # Training notebook (generates pkl files)
```

---

## ?? Data Architecture

### The 4 Pickle Files (generated by notebook)

| File | Contents | Size |
|---|---|---|
| `df.pkl` | DataFrame: `title, overview, genres, tagline, vote_average, popularity, tags` | ~28 MB |
| `indices.pkl` | `Series`: movie title ? integer row index | ~1.4 MB |
| `tfidf_matrix.pkl` | Sparse matrix `(45447 × 50000)` — each row = one movie's TF-IDF vector | ~15 MB |
| `tfidf.pkl` | Fitted `TfidfVectorizer` (50k features, English stop words) | ~1.8 MB |

### CSV Enrichment (done at server startup)

`df.pkl` only has 7 columns. On startup, `main.py` reads `movies_metadata.csv` and merges these extra columns in by matching on `title`:

| Extra Column | Source CSV format | Stored as |
|---|---|---|
| `release_date` | `"1994-09-23"` | String |
| `runtime` | `142` | Float (minutes) |
| `original_language` | `"en"` | String (ISO code) |
| `vote_count` | `8358` | Float |
| `genres` | `[{'id':18,'name':'Drama'}]` | `"Drama, Crime"` |
| `production_companies` | `[{'name':'Castle Rock Entertainment'}]` | `"Castle Rock Entertainment"` |
| `production_countries` | `[{'name':'United States of America'}]` | `"United States of America"` |

---

## ?? How the Recommender Works

### Phase 1 — Training (Jupyter Notebook)

1. **Feature Engineering** — For each movie, combine: `overview + genres + tagline + cast + director` into a single `tags` text blob
2. **TF-IDF Vectorization** — `TfidfVectorizer(max_features=50000, stop_words='english')` converts every movie's tags into a 50,000-dimensional sparse float vector
   - **TF (Term Frequency)** — how often a word appears in this movie's tags
   - **IDF (Inverse Document Frequency)** — how rare the word is across all movies (rare = more informative)
3. **Serialize** — Save `df`, `indices`, `tfidf`, `tfidf_matrix` as `.pkl` files for instant loading

### Phase 2 — Inference (FastAPI `/recommend` endpoint)

```
Query title: "Batman"
     ¦
     +- 1. Normalize: "batman" ? look up in indices.pkl ? row index i
     ¦
     +- 2. Slice query vector: query_vec = tfidf_matrix[i]   shape: (1 × 50000)
     ¦
     +- 3. Dot product (cosine sim): scores = tfidf_matrix @ query_vec.T
     ¦      Result: shape (45447,) — one score per movie
     ¦      (Cosine sim = dot product when both vectors are L2-normalized)
     ¦
     +- 4. Sort all scores descending, skip self (index == i)
     ¦
     +- 5. Take top N results
     ¦
     +- 6. Convert raw score (0.0–1.0) ? percentage (0–100%)
           Return: [{title, similarity_score%, overview, genres, vote_average, release_date}]
```

### Phase 3 — Home Page Ranking (IMDB Bayesian Formula)

For `sort_by=top_rated`, the endpoint uses the same formula IMDB publishes:

```
Weighted Score = (v / (v + m)) × R  +  (m / (v + m)) × C

  v = movie's vote_count
  m = minimum vote threshold (75th percentile of dataset, hard floor = 100 votes)
  R = movie's vote_average
  C = mean vote_average of all qualified movies
```

This prevents obscure movies with perfect 10.0 scores from a handful of votes from beating well-known classics.

---

## ?? API Endpoints

Base URL: `http://127.0.0.1:8000`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | API status, version, total movie count |
| `GET` | `/health` | Health check ? `{"status": "ok"}` |
| `GET` | `/home` | Filtered + sorted movie list |
| `GET` | `/search?query=` | Partial title search, returns up to 20 |
| `GET` | `/movie/{title}` | Full details for one movie (404 if missing) |
| `GET` | `/recommend?title=` | Top-N TF-IDF recommendations with similarity % |
| `GET` | `/genres` | All 18 unique genre names |
| `GET` | `/languages` | All unique ISO 639-1 language codes |

### `/home` query parameters

| Param | Type | Default | Options |
|---|---|---|---|
| `limit` | int | 24 | 1–100 |
| `sort_by` | string | `top_rated` | `top_rated`, `highest_rated`, `latest`, `popular` |
| `genre` | string | — | Any genre name (e.g. `Action`) |
| `language` | string | — | ISO code (e.g. `en`, `hi`, `fr`) |
| `year` | int | — | e.g. `2010` |

### Example Requests

```bash
# Top-rated Action movies in English from 2010
curl "http://127.0.0.1:8000/home?genre=Action&language=en&year=2010&sort_by=top_rated"

# Search for Batman movies
curl "http://127.0.0.1:8000/search?query=batman"

# Full details for Inception
curl "http://127.0.0.1:8000/movie/Inception"

# Top 10 movies similar to The Dark Knight
curl "http://127.0.0.1:8000/recommend?title=The Dark Knight&top_n=10"
```

> Browse and try all endpoints interactively at **http://127.0.0.1:8000/docs**

---

## ?? Frontend Features

### Home View
| Section | Description |
|---|---|
| ?? Search bar | Type any partial movie name — shows autocomplete + results grid |
| ?? Top Rated | IMDB Bayesian weighted score (applies sidebar filters) |
| ? Highest Rated | Raw vote_average descending |
| ?? Latest Releases | Most recent release_date first |
| ?? Most Popular | Highest popularity score first |

### Sidebar Filters
| Filter | Description |
|---|---|
| ?? Genre | Dropdown of all 18 genres |
| ?? Language | Dropdown of all ISO language codes |
| ?? Year | Number input (0 = all years) |
| ?? Sort By | Affects all home sections simultaneously |

### Movie Detail View
- **Large detail card** — title, tagline, overview, rating badge, language badge, runtime
- **Genre tags**, production companies, countries, popularity score
- **Top 10 Similar Movies** — grid with similarity % badge and animated green progress bar
- **Click any card** to navigate to its own detail page

### Design System
| Element | Value |
|---|---|
| Background | `#0a0a0a` |
| Card surface | `#1e1e1e` gradient |
| Accent / Netflix red | `#e50914` |
| Rating badge | Gold gradient `#f5c518` |
| Similarity badge | Green gradient `#00c853 ? #00e676` |
| Font | Inter (Google Fonts) |
| Card hover | Lift + red glow + top stripe animation |

---

## ?? Troubleshooting

### `Cannot connect to API server` in Streamlit
FastAPI is not running. Start it first in a separate terminal:
```bash
python -m uvicorn main:app --reload
```

### `FileNotFoundError: df.pkl` (or any `.pkl`)
The pickle files must exist in the same directory as `main.py`. Re-run all cells in `Movie_Recommender_System.ipynb` to regenerate them.

### `InconsistentVersionWarning` from scikit-learn
Non-fatal. The `.pkl` was trained with a different scikit-learn version than what's installed. The recommender still works. To remove the warning, retrain using your current version.

### Port already in use
```powershell
# Find and kill the process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Find and kill the process on port 8501
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

### Movie not found in `/recommend?title=`
The title must exactly match an entry in `indices.pkl`. Use `/search?query=...` to find the exact title string, then copy-paste it into `/recommend`.

---

## ?? requirements.txt

```
fastapi
uvicorn
pandas
numpy
scipy
scikit-learn
streamlit
requests
```

---

*100% offline — no internet required after initial pip install.*
