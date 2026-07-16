"""
Movie Recommender — Streamlit Frontend
=======================================
Netflix-inspired dark UI. Fully offline — no TMDB, no posters.
"""

import html as _html
import requests
import streamlit as st

# =============================================================================
# CONFIG
# =============================================================================
API_BASE = "http://127.0.0.1:8001"

st.set_page_config(
    page_title="🎬 CineMatch — Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# NETFLIX-DARK CSS
# =============================================================================
st.markdown("""
<style>
    /* ---------- Import Google Font ---------- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ---------- Global Theme ---------- */
    .stApp {
        background-color: #0a0a0a;
        font-family: 'Inter', sans-serif;
    }

    /* Hide default Streamlit header/footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ---------- Main Container ---------- */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* ---------- Sidebar ---------- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
        border-right: 1px solid rgba(229, 9, 20, 0.2);
    }

    [data-testid="stSidebar"] .stMarkdown h2,
    [data-testid="stSidebar"] .stMarkdown h3 {
        color: #e50914 !important;
        font-weight: 700;
    }

    [data-testid="stSidebar"] label {
        color: #b0b0b0 !important;
        font-weight: 500;
    }

    /* ---------- Title ---------- */
    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #e50914, #ff6b6b, #e50914);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.2rem;
        letter-spacing: -1px;
    }

    .hero-subtitle {
        color: #888;
        text-align: center;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
        font-weight: 300;
    }

    /* ---------- Section Headers ---------- */
    .section-header {
        color: #ffffff;
        font-size: 1.5rem;
        font-weight: 700;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #e50914;
        display: inline-block;
    }

    /* ---------- Movie Card ---------- */
    .movie-card {
        background: linear-gradient(145deg, #1e1e1e, #252525);
        border: 1px solid #333;
        border-radius: 16px;
        padding: 1.4rem;
        margin-bottom: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
        min-height: 280px;
    }

    .movie-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #e50914, #ff6b6b);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    .movie-card:hover {
        transform: translateY(-6px);
        border-color: #e50914;
        box-shadow: 0 12px 40px rgba(229, 9, 20, 0.2);
    }

    .movie-card:hover::before {
        opacity: 1;
    }

    /* ---------- Card Elements ---------- */
    .card-title {
        color: #ffffff;
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        line-height: 1.3;
    }

    .card-overview {
        color: #999;
        font-size: 0.85rem;
        line-height: 1.5;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
        margin-top: 0.6rem;
    }

    .card-meta {
        color: #777;
        font-size: 0.82rem;
        margin-top: 0.3rem;
    }

    /* ---------- Badges ---------- */
    .rating-badge {
        display: inline-block;
        background: linear-gradient(135deg, #f5c518, #e6a817);
        color: #000;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 700;
        margin-right: 6px;
    }

    .genre-tag {
        display: inline-block;
        background: rgba(229, 9, 20, 0.15);
        color: #e50914;
        border: 1px solid rgba(229, 9, 20, 0.3);
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
        margin: 2px 3px 2px 0;
    }

    .similarity-badge {
        display: inline-block;
        background: linear-gradient(135deg, #00c853, #00e676);
        color: #000;
        padding: 3px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 700;
    }

    .lang-badge {
        display: inline-block;
        background: rgba(100, 100, 255, 0.15);
        color: #8888ff;
        border: 1px solid rgba(100, 100, 255, 0.3);
        padding: 2px 8px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
    }

    /* ---------- Film Placeholder ---------- */
    .film-placeholder {
        background: linear-gradient(145deg, #2a2a2a, #1a1a1a);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        height: 180px;
        margin-bottom: 0.8rem;
        border: 1px dashed #444;
    }

    .film-icon {
        font-size: 3.5rem;
        opacity: 0.4;
    }

    /* ---------- Detail Card (large) ---------- */
    .detail-card {
        background: linear-gradient(145deg, #1a1a1a, #222);
        border: 1px solid #333;
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 1.5rem;
    }

    .detail-title {
        color: #fff;
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }

    .detail-tagline {
        color: #e50914;
        font-size: 1rem;
        font-style: italic;
        margin-bottom: 1rem;
        font-weight: 300;
    }

    .detail-overview {
        color: #ccc;
        font-size: 1rem;
        line-height: 1.7;
        margin-top: 1rem;
    }

    .detail-meta-row {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 0.8rem;
        align-items: center;
    }

    .detail-meta-item {
        color: #aaa;
        font-size: 0.9rem;
    }

    .detail-meta-item strong {
        color: #ddd;
    }

    /* ---------- Similarity Bar ---------- */
    .sim-bar-container {
        background: #333;
        border-radius: 10px;
        height: 8px;
        margin-top: 6px;
        overflow: hidden;
    }

    .sim-bar-fill {
        height: 100%;
        border-radius: 10px;
        background: linear-gradient(90deg, #e50914, #00e676);
        transition: width 0.8s ease;
    }

    /* ---------- Divider ---------- */
    .custom-divider {
        border: none;
        border-top: 1px solid #333;
        margin: 1.5rem 0;
    }

    /* ---------- Status / Error ---------- */
    .status-box {
        background: rgba(229, 9, 20, 0.1);
        border: 1px solid rgba(229, 9, 20, 0.3);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        color: #ff6b6b;
        text-align: center;
        margin: 1rem 0;
    }

    .success-box {
        background: rgba(0, 200, 83, 0.1);
        border: 1px solid rgba(0, 200, 83, 0.3);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        color: #00c853;
        text-align: center;
        margin: 1rem 0;
    }

    /* ---------- Streamlit overrides ---------- */
    .stTextInput > div > div > input {
        background-color: #1e1e1e !important;
        color: #fff !important;
        border: 2px solid #333 !important;
        border-radius: 12px !important;
        padding: 0.8rem 1rem !important;
        font-size: 1.05rem !important;
        transition: border-color 0.3s ease !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #e50914 !important;
        box-shadow: 0 0 15px rgba(229, 9, 20, 0.2) !important;
    }

    .stSelectbox > div > div {
        background-color: #1e1e1e !important;
        border-color: #333 !important;
        border-radius: 10px !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #e50914, #b20710) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 4px 20px rgba(229, 9, 20, 0.4) !important;
    }

    div[data-testid="stExpander"] {
        background: #1a1a1a;
        border: 1px solid #333;
        border-radius: 12px;
    }

    .stSlider > div > div > div {
        color: #e50914 !important;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE
# =============================================================================
if "view" not in st.session_state:
    st.session_state.view = "home"
if "selected_title" not in st.session_state:
    st.session_state.selected_title = None


def goto_home():
    st.session_state.view = "home"
    st.session_state.selected_title = None
    st.rerun()


def goto_details(title: str):
    st.session_state.view = "details"
    st.session_state.selected_title = title
    st.rerun()


# =============================================================================
# API HELPERS
# =============================================================================
@st.cache_data(ttl=60)
def api_get(path: str, params: dict = None):
    """Call local FastAPI and return (data, error)."""
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=15)
        if r.status_code >= 400:
            return None, f"HTTP {r.status_code}: {r.text[:300]}"
        return r.json(), None
    except requests.ConnectionError:
        return None, "Cannot connect to API server. Make sure FastAPI is running on port 8000."
    except Exception as e:
        return None, str(e)


# =============================================================================
# RENDER HELPERS
# =============================================================================
def render_genre_tags(genres_str: str) -> str:
    """Convert a genres string (comma or space-separated) into HTML genre tags."""
    if not genres_str:
        return ""
    s = str(genres_str).strip()
    if "," in s:
        # Comma-separated (CSV-enriched data)
        parts = [g.strip() for g in s.split(",") if g.strip()]
    else:
        # Space-separated from df.pkl — preserve known multi-word genres
        for mw, ph in [("Science Fiction", "SciFi__"), ("TV Movie", "TVMovie__")]:
            s = s.replace(mw, ph)
        parts = [p.replace("SciFi__", "Science Fiction").replace("TVMovie__", "TV Movie")
                 for p in s.split() if p]
    return " ".join(f"<span class='genre-tag'>{_html.escape(g)}</span>" for g in parts[:4])


def render_movie_card(movie: dict, show_similarity: bool = False):
    """
    Render a single movie card as a compact single-line HTML string.
    Compact format prevents Streamlit's Markdown parser from treating
    blank lines inside multi-line HTML as paragraph breaks.
    """
    title = _html.escape(str(movie.get("title", "Untitled")))
    rating = movie.get("vote_average")
    genres = movie.get("genres", "")
    overview = movie.get("overview", "")
    release = movie.get("release_date", "")
    similarity = movie.get("similarity_score", 0)
    language = movie.get("language", "")

    year = str(release)[:4] if release else ""
    rating_html = f"<span class='rating-badge'>⭐ {rating:.1f}</span>" if rating else ""
    genre_html = render_genre_tags(genres)
    lang_html = f"<span class='lang-badge'>{_html.escape(language.upper())}</span>" if language else ""

    sim_html = ""
    if show_similarity and similarity:
        bar_w = min(float(similarity), 100.0)
        sim_html = (
            f"<div style='margin-top:8px;'>"
            f"<span class='similarity-badge'>{similarity:.1f}% Match</span>"
            f"<div class='sim-bar-container'>"
            f"<div class='sim-bar-fill' style='width:{bar_w:.1f}%;'></div>"
            f"</div></div>"
        )

    overview_short = str(overview)[:150] + "..." if overview and len(str(overview)) > 150 else (overview or "")

    return (
        f"<div class='movie-card'>"
        f"<div class='film-placeholder'><span class='film-icon'>🎬</span></div>"
        f"<div class='card-title'>{title}</div>"
        f"<div>{rating_html}{lang_html}<span class='card-meta'>{year}</span></div>"
        f"<div style='margin-top:6px;'>{genre_html}</div>"
        f"{sim_html}"
        f"<div class='card-overview'>{_html.escape(overview_short)}</div>"
        f"</div>"
    )


def render_movie_grid(movies: list, cols: int = 4, show_similarity: bool = False, clickable: bool = True, key_prefix: str = "grid"):
    """Render a grid of movie cards with optional click-to-detail buttons."""
    if not movies:
        st.markdown("<div class='status-box'>No movies found.</div>", unsafe_allow_html=True)
        return

    rows = (len(movies) + cols - 1) // cols
    idx = 0
    for r in range(rows):
        columns = st.columns(cols)
        for c in range(cols):
            if idx >= len(movies):
                break
            movie = movies[idx]
            with columns[c]:
                st.markdown(render_movie_card(movie, show_similarity=show_similarity), unsafe_allow_html=True)
                if clickable:
                    title = movie.get("title", "")
                    if st.button(f"View Details", key=f"{key_prefix}_{r}_{c}_{idx}", use_container_width=True):
                        goto_details(title)
            idx += 1


def render_detail_card(movie: dict):
    """
    Render the detailed movie information card as compact single-line HTML.
    Compact format prevents Streamlit's Markdown parser from treating
    blank lines inside multi-line HTML as paragraph breaks.
    """
    title = _html.escape(str(movie.get("title", "Untitled")))
    tagline = str(movie.get("tagline") or "")
    overview = str(movie.get("overview") or "No overview available.")
    rating = movie.get("vote_average")
    genres = movie.get("genres", "")
    release = movie.get("release_date", "N/A")
    language = movie.get("original_language", "")
    runtime = movie.get("runtime")
    popularity = movie.get("popularity")
    prod_companies = str(movie.get("production_companies") or "")
    prod_countries = str(movie.get("production_countries") or "")

    rating_html = f"<span class='rating-badge'>⭐ {rating:.1f} / 10</span>" if rating else ""
    genre_html = render_genre_tags(genres)
    runtime_html = (f"<span class='detail-meta-item'><strong>🕐 Runtime:</strong> {int(runtime)} min</span>"
                    if runtime else "")
    lang_html = f"<span class='lang-badge'>{_html.escape(language.upper())}</span>" if language else ""
    tagline_html = (f"<div class='detail-tagline'>&quot;{_html.escape(tagline)}&quot;</div>"
                    if tagline else "")
    popularity_html = (f"<span class='detail-meta-item'><strong>📈 Popularity:</strong> {popularity:.1f}</span>"
                       if popularity else "")
    companies_html = (f"<span class='detail-meta-item'><strong>🏢 Studios:</strong> {_html.escape(prod_companies)}</span>"
                      if prod_companies else "")
    countries_html = (f"<span class='detail-meta-item'><strong>🌍 Countries:</strong> {_html.escape(prod_countries)}</span>"
                      if prod_countries else "")

    html = (
        f"<div class='detail-card'>"
        f"<div style='display:flex;gap:2rem;flex-wrap:wrap;'>"
        f"<div style='flex:0 0 200px;'>"
        f"<div class='film-placeholder' style='height:280px;'>"
        f"<span class='film-icon' style='font-size:5rem;'>🎬</span>"
        f"</div></div>"
        f"<div style='flex:1;min-width:300px;'>"
        f"<div class='detail-title'>{title}</div>"
        f"{tagline_html}"
        f"<div class='detail-meta-row'>"
        f"{rating_html}{lang_html}"
        f"<span class='detail-meta-item'><strong>📅</strong> {release}</span>"
        f"{runtime_html}"
        f"</div>"
        f"<div style='margin-top:10px;'>{genre_html}</div>"
        f"<div class='detail-overview'>{_html.escape(overview)}</div>"
        f"<hr class='custom-divider'>"
        f"<div class='detail-meta-row'>{popularity_html}{companies_html}{countries_html}</div>"
        f"</div></div></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


# =============================================================================
# SIDEBAR
# =============================================================================
with st.sidebar:
    st.markdown("## 🎬 CineMatch")
    st.markdown("<p style='color: #888; font-size: 0.85rem;'>Offline Movie Recommender</p>", unsafe_allow_html=True)

    st.markdown("---")

    if st.button("🏠 Home", use_container_width=True):
        goto_home()

    st.markdown("---")
    st.markdown("### 🎛️ Filters")

    # Genre filter
    genres_list, _ = api_get("/genres")
    genre_options = ["All"] + (genres_list if genres_list else [])
    selected_genre = st.selectbox("🎭 Genre", genre_options, index=0)

    # Language filter
    langs_list, _ = api_get("/languages")
    lang_options = ["All"] + (langs_list if langs_list else [])
    selected_language = st.selectbox("🌐 Language", lang_options, index=0)

    # Year filter (0 = all years)
    selected_year = st.number_input("📅 Year", min_value=0, max_value=2026, value=0, step=1,
                                     help="Set to 0 for all years")

    # Sort
    sort_options = {
        "Top Rated (Weighted)": "top_rated",
        "Highest Rating": "highest_rated",
        "Latest Releases": "latest",
        "Most Popular": "popular",
    }
    selected_sort_label = st.selectbox("📊 Sort By", list(sort_options.keys()), index=0)
    selected_sort = sort_options[selected_sort_label]

    st.markdown("---")
    st.markdown("<p style='color: #555; font-size: 0.75rem; text-align: center;'>Powered by TF-IDF &amp; Cosine Similarity<br>100% Offline</p>", unsafe_allow_html=True)


# =============================================================================
# HEADER
# =============================================================================
st.markdown("<div class='hero-title'>🎬 CineMatch</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-subtitle'>Discover movies you'll love — powered by AI, completely offline</div>", unsafe_allow_html=True)


# =============================================================================
# VIEW: HOME
# =============================================================================
if st.session_state.view == "home":

    # ----- Search Bar -----
    search_query = st.text_input(
        "🔍 Search Movies",
        placeholder="Type a movie name... (e.g. Batman, Inception, Love)",
        label_visibility="collapsed",
    )

    # ----- Autocomplete + Search Results -----
    if search_query and len(search_query.strip()) >= 1:
        with st.spinner("Searching..."):
            results, err = api_get("/search", params={"query": search_query.strip(), "limit": 20})

        if err:
            st.markdown(f"<div class='status-box'>⚠️ {err}</div>", unsafe_allow_html=True)
        elif not results:
            st.markdown("<div class='status-box'>No movies found. Try a different search term.</div>", unsafe_allow_html=True)
        else:
            # Autocomplete dropdown
            titles = [r["title"] for r in results]
            labels = []
            for r in results:
                year = str(r.get("release_date", ""))[:4]
                rating = r.get("vote_average")
                lbl = r["title"]
                if year:
                    lbl += f" ({year})"
                if rating:
                    lbl += f" — ⭐ {rating:.1f}"
                labels.append(lbl)

            selected_label = st.selectbox(
                "Select a movie:",
                ["— Select a movie —"] + labels,
                index=0,
            )

            if selected_label != "— Select a movie —":
                # Map label back to title
                label_idx = labels.index(selected_label)
                goto_details(titles[label_idx])

            # Show search results as cards
            st.markdown("<div class='section-header'>🔍 Search Results</div>", unsafe_allow_html=True)
            render_movie_grid(results, cols=4, clickable=True, key_prefix="search")

    else:
        # ----- Home Sections -----

        # Build filter params
        home_params = {"limit": 24, "sort_by": selected_sort}
        if selected_genre != "All":
            home_params["genre"] = selected_genre
        if selected_language != "All":
            home_params["language"] = selected_language
        if selected_year and selected_year > 0:
            home_params["year"] = selected_year

        # Section 1: Top Rated
        st.markdown("<div class='section-header'>🏆 Top Rated Movies</div>", unsafe_allow_html=True)
        top_rated, err = api_get("/home", params={**home_params, "sort_by": "top_rated", "limit": 12})
        if err:
            st.markdown(f"<div class='status-box'>⚠️ {err}</div>", unsafe_allow_html=True)
        else:
            render_movie_grid(top_rated or [], cols=4, clickable=True, key_prefix="top_rated")

        st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

        # Section 2: Highest Rated
        st.markdown("<div class='section-header'>⭐ Highest Rated</div>", unsafe_allow_html=True)
        highest, err2 = api_get("/home", params={**home_params, "sort_by": "highest_rated", "limit": 8})
        if err2:
            st.markdown(f"<div class='status-box'>⚠️ {err2}</div>", unsafe_allow_html=True)
        else:
            render_movie_grid(highest or [], cols=4, clickable=True, key_prefix="highest")

        st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

        # Section 3: Latest
        st.markdown("<div class='section-header'>🆕 Latest Releases</div>", unsafe_allow_html=True)
        latest, err3 = api_get("/home", params={**home_params, "sort_by": "latest", "limit": 8})
        if err3:
            st.markdown(f"<div class='status-box'>⚠️ {err3}</div>", unsafe_allow_html=True)
        else:
            render_movie_grid(latest or [], cols=4, clickable=True, key_prefix="latest")

        st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

        # Section 4: Most Popular
        st.markdown("<div class='section-header'>🔥 Most Popular</div>", unsafe_allow_html=True)
        popular, err4 = api_get("/home", params={**home_params, "sort_by": "popular", "limit": 8})
        if err4:
            st.markdown(f"<div class='status-box'>⚠️ {err4}</div>", unsafe_allow_html=True)
        else:
            render_movie_grid(popular or [], cols=4, clickable=True, key_prefix="popular")


# =============================================================================
# VIEW: DETAILS
# =============================================================================
elif st.session_state.view == "details":
    title = st.session_state.selected_title

    if not title:
        st.markdown("<div class='status-box'>No movie selected.</div>", unsafe_allow_html=True)
        if st.button("← Back to Home"):
            goto_home()
        st.stop()

    # Back button
    col_back, col_spacer = st.columns([1, 5])
    with col_back:
        if st.button("← Back to Home", use_container_width=True):
            goto_home()

    # Fetch movie details
    with st.spinner("Loading movie details..."):
        details, err = api_get(f"/movie/{title}")

    if err or not details:
        st.markdown(f"<div class='status-box'>⚠️ Could not load movie details: {err or 'Unknown error'}</div>", unsafe_allow_html=True)
        st.stop()

    # Render detail card
    render_detail_card(details)

    # ----- Recommendations -----
    st.markdown("<div class='section-header'>🎯 Top 10 Similar Movies</div>", unsafe_allow_html=True)

    with st.spinner("Computing recommendations..."):
        recs, rec_err = api_get("/recommend", params={"title": title, "top_n": 10})

    if rec_err:
        st.markdown(f"<div class='status-box'>⚠️ {rec_err}</div>", unsafe_allow_html=True)
    elif not recs:
        st.markdown("<div class='status-box'>No recommendations available for this movie.</div>", unsafe_allow_html=True)
    else:
        render_movie_grid(recs, cols=4, show_similarity=True, clickable=True, key_prefix="recs")