from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "mysql+aiomysql://root:laxman@localhost:3306/iot"

# Create an async engine
engine: AsyncEngine = create_async_engine(DATABASE_URL, echo=True)

# Create an async session factory
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Base class for models
Base = declarative_base()

# Dependency function to use in FastAPI
async def get_async_session() -> AsyncSession:
    async with async_session() as session:
        yield session
