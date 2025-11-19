"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Claude Feedback Analyzer schema
class Feedback(BaseModel):
    """
    Feedback submissions about Claude responses
    Collection name: "feedback"
    """
    question: str = Field(..., min_length=5, max_length=2000, description="The user's original question")
    response: str = Field(..., min_length=5, max_length=20000, description="Claude's response text")
    improvement: str = Field(..., min_length=3, max_length=20000, description="What Claude should have done better")
    category: Literal[
        "Misunderstanding",
        "Too Verbose",
        "Inaccurate",
        "Missing Context",
        "Hallucination",
        "Tone",
        "Other",
    ] = Field(..., description="Issue category")
    severity: Optional[Literal["low", "medium", "high"]] = Field(
        default="medium", description="Optional severity label"
    )
