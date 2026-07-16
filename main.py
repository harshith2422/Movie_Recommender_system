"""
Movie Recommender API — Fully Offline
======================================
No external API calls. All data from local pickle files + movies_metadata.csv.
"""

import ast
import os
import pickle
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# =============================================================================
# FASTAPI APP
# =============================================================================
app = FastAPI(
    title="Movie Recommender API",
    description="Fully offline movie recommendation engine powered by TF-IDF.",
    version="4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# FILE PATHS
# =============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DF_PATH = os.path.join(BASE_DIR, "df.pkl")
INDICES_PATH = os.path.join(BASE_DIR, "indices.pkl")
TFIDF_MATRIX_PATH = os.path.join(BASE_DIR, "tfidf_matrix.pkl")
TFIDF_PATH = os.path.join(BASE_DIR, "tfidf.pkl")
CSV_PATH = os.path.join(BASE_DIR, "movies_metadata.csv")


# =============================================================================
# GLOBALS (populated at startup)
# =============================================================================
df: Optional[pd.DataFrame] = None
tfidf_matrix: Any = None
tfidf_obj: Any = None
TITLE_TO_IDX: Optional[Dict[str, int]] = None


# =============================================================================
# PYDANTIC MODELS
# =============================================================================
class MovieCard(BaseModel):
    """Lightweight movie representation for lists and grids."""
    title: str
    overview: Optional[str] = None
    genres: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None
    popularity: Optional[float] = None
    language: Optional[str] = None
    runtime: Optional[float] = None


class MovieDetails(BaseModel):
    """Full movie details for the detail page."""
    title: str
    overview: Optional[str] = None
    genres: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: Optional[float] = None
    popularity: Optional[float] = None
    original_language: Optional[str] = None
    runtime: Optional[float] = None
    tagline: Optional[str] = None
    production_companies: Optional[str] = None
    production_countries: Optional[str] = None


class RecommendationItem(BaseModel):
    """A single recommendation with similarity score."""
    title: str
    similarity_score: float  # percentage (0–100)
    overview: Optional[str] = None
    genres: Optional[str] = None
    vote_average: Optional[float] = None
    release_date: Optional[str] = None


# =============================================================================
# HELPERS
# =============================================================================
def _norm(text: str) -> str:
    """Normalize a string for case-insensitive comparison."""
    return str(text).strip().lower()


def _safe_float(val: Any) -> Optional[float]:
    """Convert a value to float, returning None on failure."""
    try:
        f = float(val)
        return f if not np.isnan(f) else None
    except (ValueError, TypeError):
        return None


def _safe_str(val: Any) -> Optional[str]:
    """Convert a value to a cleaned string, returning None for NaN/empty."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    s = str(val).strip()
    return s if s and s.lower() != "nan" else None


def _parse_json_list_field(raw: Any) -> str:
    """
    Parse fields stored as stringified lists of dicts (e.g. genres,
    production_companies) and return a comma-separated string of names.
    Example: "[{'name': 'Drama', 'id': 18}]" → "Drama"
    """
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return ""
    try:
        items = ast.literal_eval(str(raw))
        if isinstance(items, list):
            names = [d["name"] for d in items if isinstance(d, dict) and "name" in d]
            return ", ".join(names)
    except (ValueError, SyntaxError):
        pass
    return str(raw).strip()


def _build_title_index(indices: Any) -> Dict[str, int]:
    """
    Build a normalized title → row-index map from indices.pkl.
    Supports both dict and pandas Series.
    """
    mapping: Dict[str, int] = {}
    try:
        for k, v in indices.items():
            mapping[_norm(k)] = int(v)
    except Exception:
        raise RuntimeError("indices.pkl must be a dict or pandas Series with .items()")
    return mapping


# =============================================================================
# STARTUP — LOAD ALL DATA
# =============================================================================
@app.on_event("startup")
def load_data():
    global df, tfidf_matrix, tfidf_obj, TITLE_TO_IDX

    # ------ validate files exist ------
    required_files = {
        "df.pkl": DF_PATH,
        "indices.pkl": INDICES_PATH,
        "tfidf_matrix.pkl": TFIDF_MATRIX_PATH,
        "tfidf.pkl": TFIDF_PATH,
        "movies_metadata.csv": CSV_PATH,
    }
    for name, path in required_files.items():
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Required file missing: {name} (expected at {path})")

    # ------ load pickle files ------
    with open(DF_PATH, "rb") as f:
        df = pickle.load(f)

    with open(INDICES_PATH, "rb") as f:
        indices_obj = pickle.load(f)

    with open(TFIDF_MATRIX_PATH, "rb") as f:
        tfidf_matrix = pickle.load(f)

    with open(TFIDF_PATH, "rb") as f:
        tfidf_obj = pickle.load(f)

    # ------ sanity checks ------
    if df is None or "title" not in df.columns:
        raise RuntimeError("df.pkl must be a DataFrame with a 'title' column")

    # ------ enrich df with CSV columns ------
    csv_df = pd.read_csv(CSV_PATH, low_memory=False)

    # The CSV has some corrupted rows where 'id' is a date string — drop those
    csv_df = csv_df[pd.to_numeric(csv_df.get("id", pd.Series(dtype="str")), errors="coerce").notna()]

    # Parse JSON-like fields from CSV into clean strings
    for col in ["genres", "production_companies", "production_countries"]:
        if col in csv_df.columns:
            csv_df[col + "_parsed"] = csv_df[col].apply(_parse_json_list_field)

    # Build a lookup by title (first occurrence wins) for enrichment
    csv_df["_title_norm"] = csv_df["title"].apply(lambda t: _norm(str(t)) if pd.notna(t) else "")
    csv_lookup = csv_df.drop_duplicates(subset="_title_norm", keep="first").set_index("_title_norm")

    # Add enrichment columns to df
    df["_title_norm"] = df["title"].apply(lambda t: _norm(str(t)))

    enrich_cols = {
        "release_date": "release_date",
        "runtime": "runtime",
        "original_language": "original_language",
        "vote_count": "vote_count",
        "production_companies_parsed": "production_companies",
        "production_countries_parsed": "production_countries",
        "genres_parsed": "genres_csv",
    }
    for csv_col, df_col in enrich_cols.items():
        if csv_col in csv_lookup.columns:
            df[df_col] = df["_title_norm"].map(csv_lookup[csv_col])

    # Convert types
    df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce").fillna(0.0)
    df["vote_average"] = pd.to_numeric(df["vote_average"], errors="coerce").fillna(0.0)
    df["vote_count"] = pd.to_numeric(df.get("vote_count", 0), errors="coerce").fillna(0.0)
    df["runtime"] = pd.to_numeric(df.get("runtime", pd.Series(dtype="float")), errors="coerce")

    # Build title → index map
    TITLE_TO_IDX = _build_title_index(indices_obj)

    print(f"[OK] Loaded {len(df)} movies, {len(TITLE_TO_IDX)} indexed titles, "
          f"TF-IDF matrix shape: {tfidf_matrix.shape}")


# =============================================================================
# INTERNAL QUERY HELPERS
# =============================================================================
def _row_to_card(row: pd.Series) -> dict:
    """Convert a DataFrame row to a MovieCard dict."""
    return MovieCard(
        title=_safe_str(row.get("title")) or "Untitled",
        overview=_safe_str(row.get("overview")),
        genres=_safe_str(row.get("genres")),
        release_date=_safe_str(row.get("release_date")),
        vote_average=_safe_float(row.get("vote_average")),
        popularity=_safe_float(row.get("popularity")),
        language=_safe_str(row.get("original_language")),
        runtime=_safe_float(row.get("runtime")),
    ).model_dump()


def _row_to_details(row: pd.Series) -> dict:
    """Convert a DataFrame row to a MovieDetails dict."""
    return MovieDetails(
        title=_safe_str(row.get("title")) or "Untitled",
        overview=_safe_str(row.get("overview")),
        genres=_safe_str(row.get("genres")),
        release_date=_safe_str(row.get("release_date")),
        vote_average=_safe_float(row.get("vote_average")),
        popularity=_safe_float(row.get("popularity")),
        original_language=_safe_str(row.get("original_language")),
        runtime=_safe_float(row.get("runtime")),
        tagline=_safe_str(row.get("tagline")),
        production_companies=_safe_str(row.get("production_companies")),
        production_countries=_safe_str(row.get("production_countries")),
    ).model_dump()


def _get_idx(title: str) -> int:
    """Look up the TF-IDF matrix row index for a given title."""
    if TITLE_TO_IDX is None:
        raise HTTPException(status_code=500, detail="TF-IDF index not initialized")
    key = _norm(title)
    if key in TITLE_TO_IDX:
        return TITLE_TO_IDX[key]
    raise HTTPException(status_code=404, detail=f"Title not in dataset: '{title}'")


def _compute_recommendations(
    query_title: str, top_n: int = 10
) -> List[Tuple[int, str, float]]:
    """
    Compute TF-IDF cosine-similarity recommendations.
    Returns list of (row_index, title, score) tuples.
    """
    if df is None or tfidf_matrix is None:
        raise HTTPException(status_code=500, detail="TF-IDF resources not loaded")

    idx = _get_idx(query_title)
    query_vec = tfidf_matrix[idx]
    scores = (tfidf_matrix @ query_vec.T).toarray().ravel()

    # Sort descending, skip self
    order = np.argsort(-scores)
    results: List[Tuple[int, str, float]] = []
    for i in order:
        i = int(i)
        if i == idx:
            continue
        try:
            title_i = str(df.iloc[i]["title"])
        except (IndexError, KeyError):
            continue
        results.append((i, title_i, float(scores[i])))
        if len(results) >= top_n:
            break
    return results


# =============================================================================
# ROUTES
# =============================================================================
@app.get("/")
def root():
    """API status."""
    return {
        "name": "Movie Recommender API",
        "version": "4.0",
        "mode": "offline",
        "status": "running",
        "total_movies": len(df) if df is not None else 0,
    }


@app.get("/health")
def health():
    """Server health check."""
    return {"status": "ok"}


# ---------- HOME ----------
@app.get("/home", response_model=List[MovieCard])
def home(
    limit: int = Query(24, ge=1, le=100),
    sort_by: str = Query("top_rated", pattern="^(top_rated|highest_rated|latest|popular)$"),
    genre: Optional[str] = Query(None, description="Filter by genre (case-insensitive partial match)"),
    language: Optional[str] = Query(None, description="Filter by original_language code (e.g. 'en')"),
    year: Optional[int] = Query(None, description="Filter by release year"),
):
    """
    Home feed — returns movies from the local dataset.

    sort_by options:
    - top_rated: balanced score (vote_average weighted by vote_count)
    - highest_rated: pure vote_average descending
    - latest: most recent release_date
    - popular: highest popularity
    """
    if df is None:
        raise HTTPException(status_code=500, detail="Dataset not loaded")

    subset = df.copy()

    # --- Filters ---
    if genre:
        genre_lower = genre.strip().lower()
        # Genres in df.pkl are space-separated (e.g. "Action Adventure Thriller")
        # Use word-boundary matching to avoid partial matches
        subset = subset[
            subset["genres"].fillna("").str.lower().str.contains(
                r'(?:^|\s)' + genre_lower + r'(?:\s|$)', na=False, regex=True
            )
        ]

    if language:
        lang_lower = language.strip().lower()
        subset = subset[
            subset["original_language"].fillna("").str.lower() == lang_lower
        ]

    if year:
        subset = subset[
            subset["release_date"].fillna("").str.startswith(str(year))
        ]

    if subset.empty:
        return []

    # --- Sorting ---
    if sort_by == "top_rated":
        # IMDB-style weighted rating (Bayesian average).
        # Require at least the 75th-percentile vote count OR 100 votes
        # to prevent obscure movies with perfect-but-sparse scores from
        # dominating the top of the list.
        p75 = subset["vote_count"].quantile(0.75)
        min_votes = max(p75, 100)
        qualified = subset[subset["vote_count"] >= min_votes].copy()
        if qualified.empty:
            qualified = subset.copy()
        C = qualified["vote_average"].mean()   # mean rating across qualified pool
        m = min_votes                           # confidence weight
        qualified["weighted_score"] = (
            (qualified["vote_count"] / (qualified["vote_count"] + m)) * qualified["vote_average"]
            + (m / (qualified["vote_count"] + m)) * C
        )
        qualified = qualified.sort_values("weighted_score", ascending=False)
        return [_row_to_card(qualified.iloc[i]) for i in range(min(limit, len(qualified)))]

    elif sort_by == "highest_rated":
        subset = subset.sort_values("vote_average", ascending=False)

    elif sort_by == "latest":
        subset = subset.dropna(subset=["release_date"])
        subset = subset.sort_values("release_date", ascending=False)

    elif sort_by == "popular":
        subset = subset.sort_values("popularity", ascending=False)

    return [_row_to_card(subset.iloc[i]) for i in range(min(limit, len(subset)))]


# ---------- SEARCH ----------
@app.get("/search")
def search(
    query: str = Query(..., min_length=1, description="Partial movie title to search"),
    limit: int = Query(20, ge=1, le=50),
):
    """
    Case-insensitive partial title search.
    Example: query='bat' returns 'Batman Begins', 'Batman', 'Batman Forever', etc.
    """
    if df is None:
        raise HTTPException(status_code=500, detail="Dataset not loaded")

    q = _norm(query)
    if not q:
        return []

    mask = df["title"].fillna("").str.lower().str.contains(q, na=False)
    matches = df[mask].head(limit)

    results = []
    for _, row in matches.iterrows():
        results.append({
            "title": _safe_str(row.get("title")) or "Untitled",
            "release_date": _safe_str(row.get("release_date")),
            "vote_average": _safe_float(row.get("vote_average")),
            "genres": _safe_str(row.get("genres")),
        })
    return results


# ---------- MOVIE DETAILS ----------
@app.get("/movie/{title}", response_model=MovieDetails)
def movie_details(title: str):
    """
    Full details for a single movie by exact title.
    Returns 404 if not found.
    """
    if df is None:
        raise HTTPException(status_code=500, detail="Dataset not loaded")

    key = _norm(title)
    mask = df["title"].fillna("").str.lower() == key
    matches = df[mask]

    if matches.empty:
        raise HTTPException(status_code=404, detail=f"Movie not found: '{title}'")

    row = matches.iloc[0]
    return _row_to_details(row)


# ---------- RECOMMENDATIONS ----------
@app.get("/recommend", response_model=List[RecommendationItem])
def recommend(
    title: str = Query(..., min_length=1, description="Movie title to get recommendations for"),
    top_n: int = Query(10, ge=1, le=50),
):
    """
    Top N recommendations using the pre-trained TF-IDF matrix.
    Similarity scores are returned as percentages (0–100).
    """
    recs = _compute_recommendations(title, top_n=top_n)

    results: List[RecommendationItem] = []
    for row_idx, rec_title, raw_score in recs:
        try:
            row = df.iloc[row_idx]
        except (IndexError, KeyError):
            continue

        # Convert cosine similarity (0–1) to percentage
        similarity_pct = round(raw_score * 100, 2)

        results.append(RecommendationItem(
            title=rec_title,
            similarity_score=similarity_pct,
            overview=_safe_str(row.get("overview")),
            genres=_safe_str(row.get("genres")),
            vote_average=_safe_float(row.get("vote_average")),
            release_date=_safe_str(row.get("release_date")),
        ))

    return results


# ---------- METADATA ENDPOINTS (for frontend filters) ----------
@app.get("/genres")
def list_genres():
    """Return all unique individual genre names for filter dropdowns."""
    if df is None:
        return []
    all_genres = set()
    for g in df["genres"].dropna():
        # Genres are space-separated in df.pkl: "Action Adventure Thriller"
        # But some genre names are multi-word like "Science Fiction", "TV Movie"
        # We handle known multi-word genres explicitly
        raw = str(g)
        # Replace known multi-word genres with placeholders
        multi_word = {
            "Science Fiction": "Science_Fiction",
            "TV Movie": "TV_Movie",
        }
        for mw, placeholder in multi_word.items():
            raw = raw.replace(mw, placeholder)
        for word in raw.split():
            # Restore multi-word genres
            for mw, placeholder in multi_word.items():
                word = word.replace(placeholder, mw)
            if word:
                all_genres.add(word)
    return sorted(all_genres)


@app.get("/languages")
def list_languages():
    """Return all unique language codes for filter dropdowns."""
    if df is None:
        return []
    langs = df["original_language"].dropna().unique()
    return sorted([str(l).strip() for l in langs if str(l).strip()])