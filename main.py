import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Highscore

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Snake Game Backend Running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# Highscore Endpoints

class HighscoreCreate(BaseModel):
    name: Optional[str] = None
    score: int

class HighscoreOut(BaseModel):
    id: str
    name: Optional[str] = None
    score: int

@app.get("/api/highscore", response_model=HighscoreOut)
def get_highscore():
    """Return the top/highest score document. If none, return default 0."""
    if db is None:
        return HighscoreOut(id="", name=None, score=0)
    doc = db["highscore"].find_one(sort=[("score", -1)])
    if not doc:
        return HighscoreOut(id="", name=None, score=0)
    return HighscoreOut(
        id=str(doc.get("_id")),
        name=doc.get("name"),
        score=int(doc.get("score", 0)),
    )

@app.post("/api/highscore", response_model=HighscoreOut)
def submit_score(payload: HighscoreCreate):
    """Create a new highscore if higher than current top; else just return current top."""
    # Get current top
    top_doc = db["highscore"].find_one(sort=[("score", -1)]) if db else None
    if top_doc and payload.score <= int(top_doc.get("score", 0)):
        return HighscoreOut(id=str(top_doc.get("_id")), name=top_doc.get("name"), score=int(top_doc.get("score", 0)))

    # Insert new score
    data = {"name": payload.name, "score": int(payload.score)}
    if db is None:
        # If DB isn't available, just echo back
        return HighscoreOut(id="", name=data["name"], score=data["score"])
    inserted_id = db["highscore"].insert_one(data).inserted_id
    return HighscoreOut(id=str(inserted_id), name=data["name"], score=data["score"]) 


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
