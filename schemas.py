"""
Database Schemas for Newtonbotics Lab Store

Each Pydantic model represents a MongoDB collection. The collection name is the lowercase
of the class name (e.g., Product -> "product").
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, EmailStr


class ProductSpec(BaseModel):
    dimensions_mm: Optional[str] = Field(None, description="L x W x H in millimeters")
    weight_g: Optional[float] = Field(None, description="Weight in grams")
    materials: Optional[List[str]] = Field(default=None, description="Materials used")
    voltage_range_v: Optional[str] = Field(None, description="Voltage range, e.g. 5-12V")
    current_max_a: Optional[float] = Field(None, description="Max current in amps")
    tolerance_mm: Optional[float] = Field(None, description="Manufacturing tolerance in mm")
    mounting_pattern: Optional[str] = Field(None, description="Hole pattern or standard")
    compatibility: Optional[List[str]] = Field(default=None, description="Compatible systems/components")


class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product"
    """
    title: str = Field(..., description="Product title")
    slug: str = Field(..., description="URL-safe identifier")
    description: str = Field(..., description="Product description")
    category: Literal["3d-printed", "laser-engraved", "electronics"]
    price: float = Field(..., ge=0, description="Price in USD")
    in_stock: bool = Field(True, description="Availability flag")
    images: List[str] = Field(default_factory=list, description="Image paths under /public")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    specs: Optional[ProductSpec] = None


class OrderItem(BaseModel):
    product_id: str
    title: str
    price: float
    quantity: int = Field(..., ge=1)


class CustomerInfo(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str


class Order(BaseModel):
    """
    Orders collection schema (Pay on Delivery)
    Collection name: "order"
    """
    items: List[OrderItem]
    customer: CustomerInfo
    notes: Optional[str] = None
    subtotal: float
    shipping: float
    total: float
    payment_method: Literal["cod"] = "cod"
    status: Literal["received", "processing", "shipped", "delivered", "cancelled"] = "received"
