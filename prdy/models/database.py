"""
Database connection and session management
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from .prd import Base


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self, database_url: str = None):
        if database_url is None:
            # Default to SQLite in the project directory
            db_path = os.path.join(os.getcwd(), "prd_generator.db")
            database_url = f"sqlite:///{db_path}"
        
        self.database_url = database_url
        
        # Create engine with appropriate configuration
        if database_url.startswith("sqlite"):
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False  # Set to True for SQL debugging
            )
        else:
            self.engine = create_engine(database_url, echo=False)
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create all tables
        self.create_tables()
    
    def create_tables(self) -> None:
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """Get database session for synchronous operations"""
        return self.SessionLocal()


# Global database manager instance
db_manager: DatabaseManager = None


def init_database(database_url: str = None) -> DatabaseManager:
    """Initialize the global database manager"""
    global db_manager
    db_manager = DatabaseManager(database_url)
    return db_manager


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    if db_manager is None:
        init_database()
    yield from db_manager.get_session()


def get_db_sync() -> Session:
    """Get database session synchronously"""
    if db_manager is None:
        init_database()
    return db_manager.get_session_sync()