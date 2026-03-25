"""
Living UI API Routes

Define your API endpoints here.
"""

# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select
# from pydantic import BaseModel
# from typing import List, Optional
# from database import get_session
# from models import Item

# router = APIRouter()

# # Pydantic schemas
# class ItemCreate(BaseModel):
#     title: str
#     description: Optional[str] = None

# class ItemUpdate(BaseModel):
#     title: Optional[str] = None
#     description: Optional[str] = None
#     completed: Optional[bool] = None

# class ItemResponse(BaseModel):
#     id: int
#     title: str
#     description: Optional[str]
#     completed: bool
#     created_at: str
#     updated_at: str

# @router.get("/items", response_model=List[ItemResponse])
# async def list_items(session: AsyncSession = Depends(get_session)):
#     result = await session.execute(select(Item))
#     items = result.scalars().all()
#     return [item.to_dict() for item in items]

# @router.post("/items", response_model=ItemResponse)
# async def create_item(data: ItemCreate, session: AsyncSession = Depends(get_session)):
#     item = Item(title=data.title, description=data.description)
#     session.add(item)
#     await session.commit()
#     await session.refresh(item)
#     return item.to_dict()

# @router.get("/items/{item_id}", response_model=ItemResponse)
# async def get_item(item_id: int, session: AsyncSession = Depends(get_session)):
#     result = await session.execute(select(Item).where(Item.id == item_id))
#     item = result.scalar_one_or_none()
#     if not item:
#         raise HTTPException(status_code=404, detail="Item not found")
#     return item.to_dict()

# @router.put("/items/{item_id}", response_model=ItemResponse)
# async def update_item(
#     item_id: int,
#     data: ItemUpdate,
#     session: AsyncSession = Depends(get_session)
# ):
#     result = await session.execute(select(Item).where(Item.id == item_id))
#     item = result.scalar_one_or_none()
#     if not item:
#         raise HTTPException(status_code=404, detail="Item not found")
#
#     if data.title is not None:
#         item.title = data.title
#     if data.description is not None:
#         item.description = data.description
#     if data.completed is not None:
#         item.completed = data.completed
#
#     await session.commit()
#     await session.refresh(item)
#     return item.to_dict()

# @router.delete("/items/{item_id}")
# async def delete_item(item_id: int, session: AsyncSession = Depends(get_session)):
#     result = await session.execute(select(Item).where(Item.id == item_id))
#     item = result.scalar_one_or_none()
#     if not item:
#         raise HTTPException(status_code=404, detail="Item not found")
#
#     await session.delete(item)
#     await session.commit()
#     return {"message": "Item deleted"}

print("Living UI Routes - Uncomment and customize")
