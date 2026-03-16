from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import CuisineCreate, CuisineRead, CuisineUpdate
from models import Cuisine, db_helper


router = APIRouter(
    tags=["Cuisines"],
    prefix="/cuisines",
)


@router.post("", response_model=CuisineRead, status_code=status.HTTP_201_CREATED)
async def cuisine_create(
    cuisine_create: CuisineCreate,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Cuisine:
    stmt = select(Cuisine).where(Cuisine.name == cuisine_create.name)
    existing_cuisine = await session.scalar(stmt)
    if existing_cuisine is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cuisine with name {cuisine_create.name} already exists",
        )

    cuisine = Cuisine(name=cuisine_create.name)
    session.add(cuisine)
    await session.commit()
    await session.refresh(cuisine)
    return cuisine


@router.get("", response_model=list[CuisineRead])
async def cuisine_list(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> list[Cuisine]:
    stmt = select(Cuisine).order_by(Cuisine.id)
    cuisines = await session.scalars(stmt)
    return cuisines.all()


@router.get("/{id}", response_model=CuisineRead)
async def cuisine_read_one(
    id: int,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Cuisine:
    cuisine = await session.get(Cuisine, id)
    if cuisine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cuisine with id {id} not found",
        )
    return cuisine


@router.put("/{id}", response_model=CuisineRead)
async def cuisine_update(
    id: int,
    cuisine_update: CuisineUpdate,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Cuisine:
    cuisine = await session.get(Cuisine, id)
    if cuisine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cuisine with id {id} not found",
        )

    update_data = cuisine_update.model_dump(exclude_unset=True)
    if "name" in update_data:
        stmt = select(Cuisine).where(
            Cuisine.name == update_data["name"],
            Cuisine.id != id,
        )
        existing_cuisine = await session.scalar(stmt)
        if existing_cuisine is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cuisine with name {update_data['name']} already exists",
            )

    for field_name, value in update_data.items():
        setattr(cuisine, field_name, value)

    await session.commit()
    await session.refresh(cuisine)
    return cuisine


@router.delete("/{id}", response_model=CuisineRead)
async def cuisine_delete(
    id: int,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Cuisine:
    cuisine = await session.get(Cuisine, id)
    if cuisine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cuisine with id {id} not found",
        )

    await session.delete(cuisine)
    await session.commit()
    return cuisine
