import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents

app = FastAPI(title="Newtonbotics Lab Store API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Newtonbotics Lab Store Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "❌ Not Set",
        "database_name": "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                response["collections"] = db.list_collection_names()[:10]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "❌ Database not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# -------- Product Endpoints --------
class ProductQuery(BaseModel):
    q: Optional[str] = None
    category: Optional[str] = None  # 3d-printed | laser-engraved | electronics
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    limit: int = 30


@app.get("/api/products")
def list_products(q: Optional[str] = None, category: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None, limit: int = 30):
    """Query products by text, category, and price range"""
    filter_dict = {}
    if category:
        filter_dict["category"] = category
    if min_price is not None or max_price is not None:
        price_filter = {}
        if min_price is not None:
            price_filter["$gte"] = min_price
        if max_price is not None:
            price_filter["$lte"] = max_price
        filter_dict["price"] = price_filter
    # Simple text search on title/tags if q provided
    if q:
        filter_dict["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"tags": {"$elemMatch": {"$regex": q, "$options": "i"}}},
        ]
    try:
        products = get_documents("product", filter_dict, limit=limit)
        # Convert ObjectId to string if present
        for p in products:
            if "_id" in p:
                p["id"] = str(p.pop("_id"))
        return {"items": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/sample-seed")
def seed_sample_products():
    """Seed database with a small set of demo products if empty.
    Returns count of inserted documents."""
    try:
        existing = get_documents("product", {}, limit=1)
        if existing:
            return {"inserted": 0, "message": "Products already exist"}
        # Minimal sample data
        samples = [
            {
                "title": "Precision Servo Mount",
                "slug": "precision-servo-mount",
                "description": "CNC-accurate 3D-printed mount for standard servos with M3 hardware.",
                "category": "3d-printed",
                "price": 9.99,
                "in_stock": True,
                "images": ["/products/servo-mount-1.jpg"],
                "tags": ["mount", "3d print", "servo"],
                "specs": {
                    "dimensions_mm": "40x20x18",
                    "materials": ["PLA+"],
                    "tolerance_mm": 0.2,
                    "mounting_pattern": "M3 16mm",
                },
            },
            {
                "title": "Laser-Engraved Control Panel Plate",
                "slug": "control-panel-plate",
                "description": "Acrylic front panel with crisp vector engravings and pre-drilled holes.",
                "category": "laser-engraved",
                "price": 24.0,
                "in_stock": True,
                "images": ["/products/panel-plate-1.jpg"],
                "tags": ["panel", "acrylic", "engraved"],
                "specs": {
                    "dimensions_mm": "120x60x3",
                    "materials": ["Acrylic"],
                },
            },
            {
                "title": "Robotics Power Distribution Board",
                "slug": "pdb-12v",
                "description": "12V PDB with fused outputs, screw terminals, and status LEDs.",
                "category": "electronics",
                "price": 39.5,
                "in_stock": True,
                "images": ["/products/pdb-12v-1.jpg"],
                "tags": ["pdb", "12v", "electronics"],
                "specs": {
                    "voltage_range_v": "9-14V",
                    "current_max_a": 10.0,
                },
            },
        ]
        inserted = 0
        for s in samples:
            create_document("product", s)
            inserted += 1
        return {"inserted": inserted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class OrderItem(BaseModel):
    product_id: str
    title: str
    price: float
    quantity: int


class CustomerInfo(BaseModel):
    full_name: str
    email: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str


class OrderPayload(BaseModel):
    items: List[OrderItem]
    customer: CustomerInfo
    notes: Optional[str] = None
    subtotal: float
    shipping: float
    total: float


@app.post("/api/orders")
def create_order(payload: OrderPayload):
    """Create a Pay-on-Delivery order and return an order reference."""
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")
    order_doc = payload.model_dump()
    order_doc["payment_method"] = "cod"
    order_doc["status"] = "received"
    try:
        order_id = create_document("order", order_doc)
        return {"order_id": order_id, "status": "received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
