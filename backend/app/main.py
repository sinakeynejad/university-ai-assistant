from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import chat, documents
<<<<<<< HEAD
from .auth.database import Base, engine
from .auth.router import router as auth_router
=======
<<<<<<< HEAD
from .auth.database import Base, engine
from .auth.router import router as auth_router
=======

>>>>>>> 0dc051b2d9e72a4d21d7512f38cfc10a442035df
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2

# Load application settings
settings = get_settings()

<<<<<<< HEAD
Base.metadata.create_all(bind=engine)
=======
<<<<<<< HEAD
Base.metadata.create_all(bind=engine)
=======

>>>>>>> 0dc051b2d9e72a4d21d7512f38cfc10a442035df
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2
# Create the FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="RAG-based AI assistant prototype for K. N. Toosi University",
    version="0.1.0"
)


# Configure allowed origins for CORS
if settings.CORS_ORIGINS == "*":
    origins = ["*"]

else:
    origins = []

    # Convert comma-separated origins into a list
    origin_list = settings.CORS_ORIGINS.split(",")

    for origin in origin_list:
        origin = origin.strip()
        origins.append(origin)


# Add CORS middleware to the application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register application routers
app.include_router(chat.router)
app.include_router(documents.router)
<<<<<<< HEAD
app.include_router(auth_router)
=======
<<<<<<< HEAD
app.include_router(auth_router)
=======

>>>>>>> 0dc051b2d9e72a4d21d7512f38cfc10a442035df
>>>>>>> c8d397a7424622aef1a2556a21e0a528e6306bb2

# Health check endpoint
@app.get("/api/health", tags=["health"])
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME
    }
