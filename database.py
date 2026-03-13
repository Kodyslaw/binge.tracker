from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional

# Tworzymy plik bazy danych (SQLite)
sqlite_file_name = "binge_tracker.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)

# Definicja Tabeli Filmu (zgodnie z naszym diagramem)
class MovieCache(SQLModel, table=True):
    id: int = Field(primary_key=True)  # To będzie ID z TMDB
    title: str
    poster_url: str
    release_date: Optional[str] = None
    ai_summary: Optional[str] = None   # Tu trafi opis z Gemini
    streaming_info: Optional[str] = None # Tu trafi info z Watchmode

# Funkcja tworząca bazę danych
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()
    print("Baza danych i tabele zostały stworzone!")