import streamlit as st
import httpx
import os
from dotenv import load_dotenv
from sqlmodel import Session, select
from database import create_db_and_tables, engine, MovieCache

# 1. Konfiguracja i Klucze
load_dotenv()
TMDB_KEY = os.getenv("TMDB_API_KEY")
WATCHMODE_KEY = os.getenv("WATCHMODE_API_KEY")
OMDB_KEY = os.getenv("OMDB_API_KEY")


st.set_page_config(page_title="BingeTracker Pro", page_icon="🎬", layout="wide")

create_db_and_tables()

st.title("🎬 BingeTracker Pro")

# --- GLOBALNE MAPOWANIE DOMEN (DLA IKONEK I LINKÓW) ---
# Używane zarówno w wyszukiwarce, jak i w bibliotece

# Mapowanie Ocen (OMDb -> Dane do kafelków/mini ikonek)
RATING_MAP = {
    "Internet Movie Database": ("IMDb", "imdb.com", "https://www.imdb.com"),
    "Rotten Tomatoes": ("Rotten Tomatoes", "rottentomatoes.com", "https://www.rottentomatoes.com"),
    "Metacritic": ("Metacritic", "metacritic.com", "https://www.metacritic.com")
}

# Mapowanie Streamingu (Watchmode -> Domeny)
STREAM_MAP = {
    # Główne platformy w PL
    "Netflix": "netflix.com",
    "HBO Max": "max.com",
    "MAX": "max.com",
    "Disney+": "disneyplus.com",
    "Prime Video": "primevideo.com",
    "Apple TV+": "tv.apple.com",
    "SkyShowtime": "skyshowtime.com",
    "Player": "player.pl",
    "Canal+": "plus.canalplus.com",
    "Viaplay": "viaplay.pl",
    "Polsat Box Go": "polsatboxgo.pl",
    "TVP VOD": "vod.tvp.pl",
    
    # Platformy niszowe / kinowe / festiwalowe
    "MUBI": "mubi.com",
    "Curiosity Stream": "curiositystream.com",
    "Kino na Ekranie": "kinonaekranie.pl",
    "Cineman": "cineman.pl",
    "VOD.pl": "vod.pl",
    
    # Platformy do wypożyczenia (TVOD)
    "Google Play Movies": "play.google.com",
    "Rakuten TV": "rakuten.tv",
    "YouTube": "youtube.com",
    "Chili": "chili.com",
    "iTunes": "itunes.apple.com",
    
    # Platformy zagraniczne (jeśli korzystasz z VPN)
    "Hulu": "hulu.com",
    "Now TV": "nowtv.com",
    "Hotstar": "hotstar.com",
    "Paramount Plus": "paramountplus.com",
    "Peacock": "peacocktv.com",
    "Peacock Premium": "peacocktv.com",
    "Criterion Channel": "criterionchannel.com",
    "Movistar+": "www.movistarplus.es",
    "Sky Go": "skygo.co.nz"

}


# --- FUNKCJE API ---

def get_movie_from_tmdb(query):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={query}&language=pl-PL"
    try:
        response = httpx.get(url).json()
        return response['results'][0] if response['results'] else None
    except:
        return None

def get_streaming_providers(tmdb_id):
    url = f"https://api.watchmode.com/v1/title/movie-{tmdb_id}/sources/?regions=PL"
    params = {"apiKey": WATCHMODE_KEY}
    try:
        data = httpx.get(url, params=params).json()
        return list(set([s['name'] for s in data if s['type'] == 'sub']))
    except:
        return []

def get_omdb_ratings(title):
    url = "http://www.omdbapi.com/"
    payload = {"t": title, "apikey": OMDB_KEY}
    try:
        response = httpx.get(url, params=payload)
        # --- DEBUG START ---
        print(f"\n--- DEBUG OMDb ---")
        print(f"URL: {response.url}") # Zobaczysz dokładnie jaki link został wysłany
        print(f"Status: {response.status_code}")
        
        # Wyświetlamy to też w Streamlit, żebyś nie musiał zerkać do terminala
        # with st.expander("🛠️ Logi Debugowania API"):
        #     st.write(f"Wysłany URL: {response.url}")
        #    st.json(response.json()) # Pokaże całą surową odpowiedź z serwera
        # --- DEBUG END ---
        data = response.json()
        # POPRAWKA: OMDb używa "Ratings" (duża litera)
        if data.get("Response") == "True":
            return data
        return []
    except:
        return []
def render_mini_icon(name, domain, url):
    # Wykorzystujemy Google Favicon API, ale ustawiamy mały rozmiar w CSS
    icon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=32" # sz=32 dla lepszej jakości przy skalowaniu
    
    html = f"""
    <a href="{url}" target="_blank" title="{name}" style="text-decoration: none; margin-right: 5px; vertical-align: middle;">
        <img src="{icon_url}" width="18" height="18" style="border-radius: 2px; vertical-align: middle; border: none;">
    </a>
    """
    return html
def render_tile(name, value, domain, url):
    icon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
    tile_html = f"""
    <a href="{url}" target="_blank" style="text-decoration: none; color: inherit;">
        <div style="
            background-color: #262730;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #464b5d;
            text-align: center;
            margin-bottom: 10px;
            transition: transform 0.2s;
            cursor: pointer;
            min-height: 120px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
            <img src="{icon_url}" width="32" style="margin-bottom: 10px;">
            <div style="font-size: 0.8rem; opacity: 0.8;">{name}</div>
            <div style="font-weight: bold; font-size: 1.1rem;">{value}</div>
        </div>
    </a>
    """
    return st.markdown(tile_html, unsafe_allow_html=True)

# --- INTERFEJS UŻYTKOWNIKA ---

query = st.text_input("Wpisz tytuł filmu:", placeholder="np. Incepcja")

if query:
    movie_data = get_movie_from_tmdb(query)
    if movie_data:
        omdb_data = get_omdb_ratings(movie_data['original_title'])
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(f"https://image.tmdb.org/t/p/w500{movie_data['poster_path']}")
        
        with col2:
            st.header(movie_data['title'])
            st.caption(f"Oryginalny tytuł: {movie_data['original_title']} | 📅 {movie_data['release_date']}")
            
            with st.spinner('Pobieram dane...'):
                streaming_list = get_streaming_providers(movie_data['id'])
                ratings_list = get_omdb_ratings(movie_data['original_title'])
            if omdb_data and isinstance(omdb_data, dict):
                ratings_list = omdb_data.get("Ratings", [])
                imdb_id = omdb_data.get("imdbID")

            # --- Wyświetlanie Ocen ---
                st.subheader("⭐ Oceny")
                if ratings_list:
                    r_cols = st.columns(len(ratings_list))
                    domain_map = {
                        "Internet Movie Database": ("IMDb", "imdb.com", "https://www.imdb.com"),
                        "Rotten Tomatoes": ("Rotten Tomatoes", "rottentomatoes.com", "https://www.rottentomatoes.com"),
                        "Metacritic": ("Metacritic", "metacritic.com", "https://www.metacritic.com")
                    }
                    
                    for idx, r in enumerate(ratings_list):
                        source = r['Source']
                        
                        if source == "Internet Movie Database" and imdb_id:
                            name = "IMDb"
                            domain = "imdb.com"
                            link = f"https://www.imdb.com/title/{imdb_id}/"
                            
                        elif source == "Rotten Tomatoes":
                            name = "Rotten Tomatoes"
                            domain = "rottentomatoes.com"
                            # Twój świetny regex do czyszczenia znaków specjalnych
                            slug = movie_data['original_title'].lower().replace(" ","_").translate(str.maketrans('', '', '!@#$%^&*()[];:,./<>?\\|'))
                            link = f"https://www.rottentomatoes.com/m/{slug}"
                            
                        elif source == "Metacritic":
                            name = "Metacritic"
                            domain = "metacritic.com"
                            slug = movie_data['original_title'].lower().replace(" ","-").translate(str.maketrans('', '', '!@#$%^&*()[];:,./<>?\\|'))
                            link = f"https://www.metacritic.com/movie/{slug}"
                        
                        else:
                            name = source
                            domain = "google.com"
                            search_query = f"{movie_data['original_title']} {source} review".replace(" ", "+")
                            link = f"https://www.google.com/search?q={search_query}"
                            
                        with r_cols[idx]:
                            render_tile(name, r['Value'], domain, link)
                    else:
                        st.info("Brak ocen z api OMDb")
                else:
                    st.warning("Nie odnaleziono dodatkowych danych")
            # --- Wyświetlanie Streamingu ---
            st.subheader("📺 Dostępne w subskrypcji")
            if streaming_list:
                s_cols = st.columns(min(len(streaming_list), 4))
                stream_map = {
                    "Netflix": "netflix.com",
                    "HBO Max": "max.com",
                    "Max": "max.com",
                    "Disney+": "disneyplus.com",
                    "Prime Video": "primevideo.com",
                    "Apple TV+": "tv.apple.com",
                    "SkyShowtime": "skyshowtime.com",
                    "Player": "player.pl",
                    "Hulu": "hulu.com",
                    "Canal+": "plus.canalplus.com",
                    "Viaplay": "viaplay.pl",
                    "Rakuten TV": "rakuten.tv",
                    "YouTube": "youtube.com"
                }
                
                for idx, platform in enumerate(streaming_list):
                    if platform in STREAM_MAP:
                        domain = STREAM_MAP[platform]
                        link = f"https://{domain}"
                    else:
                        # Dynamiczne wyszukiwanie w Google dla nieznanych platform
                        domain = "google.com"
                        search_query = f"{movie_data['original_title']} {platform}".replace(" ", "+")
                        link = f"https://www.google.com/search?q={search_query}"
                        
                    with s_cols[idx % 4]:
                        render_tile(platform, "Oglądaj", domain, link)

            # --- Przycisk dodawania ---
            if st.button("➕ Dodaj do listy"):
                ratings_str = " | ".join([f"{r['Source']}: {r['Value']}" for r in ratings_list])
                streaming_str = ", ".join(streaming_list) if streaming_list else "Brak danych"
                
                with Session(engine) as session:
                    existing = session.get(MovieCache, movie_data['id'])
                    if not existing:
                        new_movie = MovieCache(
                            id=movie_data['id'],
                            title=movie_data['title'],
                            original_title=movie_data['original_title'], 
                            poster_url=movie_data['poster_path'],
                            release_date=movie_data['release_date'],
                            ai_summary=ratings_str,
                            streaming_info=streaming_str,
                            imdb_id=omdb_data.get("imdbID")              
                        )
                        session.add(new_movie)
                        session.commit()
                        st.success(f"Dodano '{movie_data['title']}' do biblioteki!")
                    else:
                        st.warning("Ten film już jest w Twojej bibliotece.")
    else:
        st.error("Nie znaleźliśmy takiego filmu.")

# --- BIBLIOTEKA ---
st.divider()
st.header("📚 Moja Biblioteka")

with Session(engine) as session:
    results = session.exec(select(MovieCache)).all()
    if results:
        cols = st.columns(4)
        for idx, m in enumerate(results):
            with cols[idx % 4]:
                st.image(f"https://image.tmdb.org/t/p/w200{m.poster_url}")
                st.subheader(m.title)
                with st.expander("Szczegóły"):
                    # 1. PRZETWARZANIE I WYŚWIETLANIE OCEN W BIBLIOTECE
                    st.write("⭐ Oceny:")
                    if m.ai_summary and m.ai_summary != "Brak danych":
                        rating_items = m.ai_summary.split(" | ")
                        html_ratings = ""
                        
                        for item in rating_items:
                            source, value = item.split(": ", 1)
                            
                            # LOGIKA LINKOWANIA IDENTYCZNA JAK W WYSZUKIWARCE
                            if source == "Internet Movie Database" and m.imdb_id:
                                name, domain = "IMDb", "imdb.com"
                                link = f"https://www.imdb.com/title/{m.imdb_id}/"
                                
                            elif source == "Rotten Tomatoes":
                                name, domain = "Rotten Tomatoes", "rottentomatoes.com"
                                # Używamy original_title z bazy do slugów
                                slug = m.original_title.lower().replace(" ","_").translate(str.maketrans('', '', '!@#$%^&*()[];:,./<>?\\|'))
                                link = f"https://www.rottentomatoes.com/m/{slug}"
                                
                            elif source == "Metacritic":
                                name, domain = "Metacritic", "metacritic.com"
                                slug = m.original_title.lower().replace(" ","-").translate(str.maketrans('', '', '!@#$%^&*()[];:,./<>?\\|'))
                                link = f"https://www.metacritic.com/movie/{slug}"
                            else:
                                # Fallback dla innych (np. Google)
                                name, domain = source, "google.com"
                                link = f"https://www.google.com/search?q={m.title}+{source}+review".replace(" ", "+")

                            # Dodajemy ikonkę i wartość
                            html_ratings += render_mini_icon(name, domain, link) + f"<span style='vertical-align: middle; margin-right: 15px; font-size: 0.9rem;'>{value}</span>"
                        
                        st.markdown(html_ratings, unsafe_allow_html=True)
                    
                    st.divider()
                    # --- 2. STREAMING W BIBLIOTECE ---
                    st.write("📺 Gdzie oglądać:")
                    if m.streaming_info and m.streaming_info != "Brak danych":
                        providers = m.streaming_info.split(", ")
                        html_stream = ""
                        
                        for platform in providers:
                            # Pobieramy domenę z naszego globalnego słownika STREAM_MAP
                            domain = STREAM_MAP.get(platform)
                            
                            if domain:
                                link = f"https://{domain}"
                            else:
                                # Fallback do Google, jeśli platformy nie ma w słowniku
                                domain = "google.com"
                                search_query = f"{m.title} {platform} online".replace(" ", "+")
                                link = f"https://www.google.com/search?q={search_query}"
                            
                            # Generujemy ikonkę
                            html_stream += render_mini_icon(platform, domain, link)
                        
                        st.markdown(html_stream, unsafe_allow_html=True)
                    else:
                        st.caption("Brak danych o streamingu")
                    
                    st.divider()

                    # Przycisk usuwania na samym dole, ładnie oddzielony
                    if st.button("🗑️ Usuń z listy", key=f"del_{m.id}", use_container_width=True):
                        with Session(engine) as session:
                            obj = session.get(MovieCache, m.id)
                            session.delete(obj)
                            session.commit()
                            st.rerun()
    else:
        st.info("Twoja lista jest pusta.")