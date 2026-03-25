"""
Living UI Python Backend

This is an optional FastAPI backend for Living UI projects.
Uncomment and customize as needed.

To run:
1. Install dependencies: pip install -r requirements.txt
2. Run server: uvicorn main:app --port {{BACKEND_PORT}} --reload
"""

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from routes import router
# from database import init_db

# app = FastAPI(
#     title="{{PROJECT_NAME}} API",
#     description="Backend API for {{PROJECT_NAME}} Living UI",
#     version="1.0.0"
# )

# # CORS configuration for frontend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include routes
# app.include_router(router, prefix="/api")

# @app.on_event("startup")
# async def startup():
#     await init_db()

# @app.get("/health")
# async def health_check():
#     return {"status": "healthy"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port={{BACKEND_PORT}})

print("Living UI Backend - Uncomment code above to enable")
