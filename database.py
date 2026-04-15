from sqlmodel import SQLModel, Field, create_engine
from typing import Optional

sqlite_file_name = "binge_tracker.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)

class MovieCache(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    
    id: int = Field(default=None, primary_key=True)
    title: str
    original_title: Optional[str] = None  
    poster_url: str
    release_date: Optional[str] = None
    ai_summary: Optional[str] = None
    streaming_info: Optional[str] = None
    imdb_id: Optional[str] = None         

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    create_db_and_tables()