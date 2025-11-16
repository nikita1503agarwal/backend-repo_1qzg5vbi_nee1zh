import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Booking

app = FastAPI(title="Assistência Técnica Remota - API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "API de Assistência Técnica Remota ativa"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
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

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# Models for responses
class BookingOut(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str]
    service_type: str
    issue_description: str
    preferred_datetime: str
    status: str
    meeting_link: Optional[str]


@app.post("/api/bookings", response_model=BookingOut)
def create_booking(booking: Booking):
    try:
        inserted_id = create_document("booking", booking)
        return BookingOut(
            id=str(inserted_id),
            name=booking.name,
            email=booking.email,
            phone=booking.phone,
            service_type=booking.service_type,
            issue_description=booking.issue_description,
            preferred_datetime=booking.preferred_datetime,
            status=booking.status,
            meeting_link=booking.meeting_link,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/bookings", response_model=List[BookingOut])
def list_bookings(status: Optional[str] = None):
    try:
        filter_dict = {"status": status} if status else {}
        docs = get_documents("booking", filter_dict=filter_dict)
        result = []
        for d in docs:
            result.append(
                BookingOut(
                    id=str(d.get("_id", "")),
                    name=d.get("name"),
                    email=d.get("email"),
                    phone=d.get("phone"),
                    service_type=d.get("service_type"),
                    issue_description=d.get("issue_description"),
                    preferred_datetime=d.get("preferred_datetime"),
                    status=d.get("status"),
                    meeting_link=d.get("meeting_link"),
                )
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
