import os
from sqlalchemy import create_engine, Column, String, JSON, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()
engine = create_engine(
    os.getenv("DATABASE_URL", "sqlite:///./artifacts/aegis.db"),
    **(
        {"connect_args": {"check_same_thread": False}}
        if os.getenv("DATABASE_URL", "sqlite").startswith("sqlite")
        else {}
    ),
)
Session = sessionmaker(engine)


class Record(Base):
    __tablename__ = "records"
    id = Column(String, primary_key=True)
    kind = Column(String, index=True, nullable=False)
    revision = Column(Integer, nullable=False, default=1)
    data = Column(JSON, nullable=False)
