import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Feedback

app = FastAPI(title="Claude Feedback Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FeedbackCreate(Feedback):
    pass


class FeedbackOut(BaseModel):
    id: str
    question: str
    response: str
    improvement: str
    category: str
    severity: Optional[str] = "medium"
    created_at: Optional[str] = None


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


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

    # Check environment variables
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Helpers

def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    doc = dict(doc)
    if doc.get("_id"):
        doc["id"] = str(doc.pop("_id"))
    # Convert datetimes to isoformat if present
    for key in ("created_at", "updated_at"):
        if key in doc and hasattr(doc[key], "isoformat"):
            doc[key] = doc[key].isoformat()
    return doc


# Feedback endpoints
@app.post("/api/feedback", response_model=Dict[str, str])
def create_feedback(payload: FeedbackCreate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    inserted_id = create_document("feedback", payload)
    return {"id": inserted_id}


@app.get("/api/feedback", response_model=List[FeedbackOut])
def list_feedback(limit: int = 50, category: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filt = {}
    if category:
        filt["category"] = category
    docs = get_documents("feedback", filt, limit)
    return [_serialize(d) for d in docs]


@app.get("/api/analytics/summary")
def analytics_summary():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    try:
        agg = list(db["feedback"].aggregate(pipeline))
        breakdown = {item["_id"] or "Unknown": item["count"] for item in agg}
        total = sum(breakdown.values())
        return {"total": total, "breakdown": breakdown}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class InsightRequest(BaseModel):
    items: List[FeedbackOut] = Field(default_factory=list)
    scope: str = Field("all", description="'week' or 'all'")


@app.post("/api/analytics/insights")
def generate_ai_insights(req: InsightRequest):
    # Mock AI generation for now. In production, call your LLM provider here.
    total = len(req.items)
    categories: Dict[str, int] = {}
    for it in req.items:
        categories[it.category] = categories.get(it.category, 0) + 1
    top = sorted(categories.items(), key=lambda x: x[1], reverse=True)

    summary_lines = [
        f"Analyzed {total} feedback item(s).",
    ]
    if top:
        head = ", ".join([f"{k}: {v}" for k, v in top[:3]])
        summary_lines.append(f"Most frequent issues: {head}.")
    if total > 0:
        summary_lines.append("Recommended actions: tighten instruction following, prefer concise answers, and ask clarifying questions when intent is ambiguous.")

    return {
        "summary": " ".join(summary_lines)
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
