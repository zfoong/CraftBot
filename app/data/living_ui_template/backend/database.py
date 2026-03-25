"""
Living UI Database Configuration

SQLite database setup with async support.
"""

# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker
# from models import Base

# DATABASE_URL = "sqlite+aiosqlite:///./living_ui.db"

# engine = create_async_engine(DATABASE_URL, echo=True)
# async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# async def init_db():
#     """Initialize database tables"""
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

# async def get_session():
#     """Dependency to get database session"""
#     async with async_session() as session:
#         try:
#             yield session
#             await session.commit()
#         except Exception:
#             await session.rollback()
#             raise

print("Living UI Database - Uncomment and customize")
