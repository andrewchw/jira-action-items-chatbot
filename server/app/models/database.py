from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, create_engine, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create SQLAlchemy base
Base = declarative_base()

# Define models
class JiraCache(Base):
    """
    Cache for Jira issues to reduce API calls
    """
    __tablename__ = "jira_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_key = Column(String(32), unique=True, index=True)
    title = Column(String(256))
    description = Column(Text, nullable=True)
    status = Column(String(64))
    assignee = Column(String(128), nullable=True)
    due_date = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    raw_data = Column(Text)  # JSON string of full issue data
    
    # Relationship with reminders
    reminders = relationship("Reminder", back_populates="jira_issue", cascade="all, delete-orphan")

class LLMCache(Base):
    """
    Cache for LLM responses to avoid repeated API calls
    """
    __tablename__ = "llm_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    prompt_hash = Column(String(64), unique=True, index=True)  # Hash of the prompt for deduplication
    prompt = Column(Text)
    response = Column(Text)
    model = Column(String(128))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # When this cache entry expires
    tokens_used = Column(Integer, default=0)
    
class Reminder(Base):
    """
    Reminders for tasks, linked to Jira issues
    """
    __tablename__ = "reminders"
    
    id = Column(Integer, primary_key=True, index=True)
    jira_issue_id = Column(Integer, ForeignKey("jira_cache.id"))
    reminder_time = Column(DateTime, index=True)
    message = Column(Text, nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(128), nullable=True)  # e.g., "daily", "weekly"
    is_sent = Column(Boolean, default=False)
    last_sent = Column(DateTime, nullable=True)
    
    # Relationship with JiraCache
    jira_issue = relationship("JiraCache", back_populates="reminders")

class UserConfig(Base):
    """
    User configuration and preferences
    """
    __tablename__ = "user_config"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(128), unique=True, index=True)
    notification_enabled = Column(Boolean, default=True)
    reminder_lead_time = Column(Integer, default=15)  # minutes before due
    last_sync = Column(DateTime, nullable=True)
    jira_token = Column(String(512), nullable=True)
    preferences = Column(Text, nullable=True)  # JSON string of preferences

# Database connection
class DatabaseManager:
    def __init__(self, db_url: Optional[str] = None):
        self.engine = None
        self.SessionLocal = None
        self.db_url = db_url or settings.DATABASE_URL
        self.init_db()
    
    def init_db(self):
        """Initialize database connection and create tables if they don't exist"""
        try:
            logger.info(f"Initializing database connection to {self.db_url}")
            self.engine = create_engine(self.db_url, connect_args={"check_same_thread": False})
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            
            # Test connection
            with self.SessionLocal() as session:
                session.execute("SELECT 1")
                logger.info("Database connection test successful")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    def get_session(self) -> Session:
        """Get a database session"""
        if not self.SessionLocal:
            raise Exception("Database not initialized")
        return self.SessionLocal()
    
    def close(self):
        """Close all connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")

# Create a database instance
db_manager = DatabaseManager()

# Dependency to use in FastAPI endpoints
def get_db():
    """
    Dependency function to get a DB session for use in FastAPI endpoints
    """
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()

# Database utility functions
def update_jira_cache(db: Session, issue_key: str, issue_data: Dict[str, Any]) -> JiraCache:
    """Update or create a cached Jira issue"""
    jira_cache = db.query(JiraCache).filter(JiraCache.issue_key == issue_key).first()
    
    if jira_cache:
        # Update existing record
        jira_cache.title = issue_data.get("title", jira_cache.title)
        jira_cache.description = issue_data.get("description", jira_cache.description)
        jira_cache.status = issue_data.get("status", jira_cache.status)
        jira_cache.assignee = issue_data.get("assignee", jira_cache.assignee)
        jira_cache.due_date = issue_data.get("due_date", jira_cache.due_date)
        jira_cache.last_updated = datetime.utcnow()
        jira_cache.raw_data = issue_data.get("raw_data", jira_cache.raw_data)
    else:
        # Create new record
        jira_cache = JiraCache(
            issue_key=issue_key,
            title=issue_data.get("title", ""),
            description=issue_data.get("description"),
            status=issue_data.get("status", ""),
            assignee=issue_data.get("assignee"),
            due_date=issue_data.get("due_date"),
            last_updated=datetime.utcnow(),
            raw_data=issue_data.get("raw_data", "{}")
        )
        db.add(jira_cache)
    
    db.commit()
    db.refresh(jira_cache)
    return jira_cache

def create_reminder(
    db: Session, 
    jira_issue_id: int, 
    reminder_time: datetime, 
    message: Optional[str] = None,
    is_recurring: bool = False,
    recurrence_pattern: Optional[str] = None
) -> Reminder:
    """Create a new reminder for a Jira issue"""
    reminder = Reminder(
        jira_issue_id=jira_issue_id,
        reminder_time=reminder_time,
        message=message,
        is_recurring=is_recurring,
        recurrence_pattern=recurrence_pattern
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder

def get_pending_reminders(db: Session) -> List[Reminder]:
    """Get all reminders that are due but not yet sent"""
    return db.query(Reminder).filter(
        Reminder.reminder_time <= datetime.utcnow(),
        Reminder.is_sent == False
    ).all()

def check_llm_cache(db: Session, prompt_hash: str) -> Optional[LLMCache]:
    """
    Check if there's a cached response for the given prompt hash
    
    Args:
        db: Database session
        prompt_hash: MD5 hash of the prompt
        
    Returns:
        Cached LLMCache object or None if not found
    """
    current_time = datetime.now()
    return db.query(LLMCache).filter(
        LLMCache.prompt_hash == prompt_hash,
        LLMCache.expires_at > current_time
    ).first()

def cache_llm_response(
    db: Session, 
    prompt: str,
    prompt_hash: str,
    response: str,
    model: str,
    tokens_used: int = 0,
    expires_at: Optional[datetime] = None
) -> LLMCache:
    """
    Cache an LLM response
    
    Args:
        db: Database session
        prompt: The original prompt string
        prompt_hash: MD5 hash of the prompt
        response: The LLM response to cache
        model: The model used for generation
        tokens_used: Number of tokens used in the request
        expires_at: When the cache entry expires (default: 24h from now)
        
    Returns:
        The created LLMCache object
    """
    if expires_at is None:
        expires_at = datetime.now() + timedelta(hours=24)
        
    # Delete any existing cache entries with the same hash
    db.query(LLMCache).filter(LLMCache.prompt_hash == prompt_hash).delete()
    
    # Create new cache entry
    cache_entry = LLMCache(
        prompt=prompt,
        prompt_hash=prompt_hash,
        response=response,
        model=model,
        tokens_used=tokens_used,
        created_at=datetime.now(),
        expires_at=expires_at
    )
    
    db.add(cache_entry)
    db.commit()
    db.refresh(cache_entry)
    
    return cache_entry

def clear_expired_llm_cache(db: Session) -> int:
    """
    Clear expired LLM cache entries
    
    Args:
        db: Database session
        
    Returns:
        Number of entries cleared
    """
    current_time = datetime.now()
    result = db.query(LLMCache).filter(LLMCache.expires_at < current_time).delete()
    db.commit()
    
    return result

def get_or_create_user_config(db: Session, user_id: str) -> UserConfig:
    """Get or create user configuration"""
    user_config = db.query(UserConfig).filter(UserConfig.user_id == user_id).first()
    if not user_config:
        user_config = UserConfig(user_id=user_id)
        db.add(user_config)
        db.commit()
        db.refresh(user_config)
    return user_config 