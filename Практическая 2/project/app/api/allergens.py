from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import AllergenCreate, AllergenRead, AllergenUpdate
from models import Allergen, db_helper


router = APIRouter(
    tags=["Allergens"],
    prefix="/allergens",
)


@router.post("", response_model=AllergenRead, status_code=status.HTTP_201_CREATED)
async def allergen_create(
    allergen_create: AllergenCreate,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Allergen:
    stmt = select(Allergen).where(Allergen.name == allergen_create.name)
    existing_allergen = await session.scalar(stmt)
    if existing_allergen is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Allergen with name {allergen_create.name} already exists",
        )

    allergen = Allergen(name=allergen_create.name)
    session.add(allergen)
    await session.commit()
    await session.refresh(allergen)
    return allergen


@router.get("", response_model=list[AllergenRead])
async def allergen_list(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> list[Allergen]:
    stmt = select(Allergen).order_by(Allergen.id)
    allergens = await session.scalars(stmt)
    return allergens.all()


@router.get("/{id}", response_model=AllergenRead)
async def allergen_read_one(
    id: int,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Allergen:
    allergen = await session.get(Allergen, id)
    if allergen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allergen with id {id} not found",
        )
    return allergen


@router.put("/{id}", response_model=AllergenRead)
async def allergen_update(
    id: int,
    allergen_update: AllergenUpdate,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Allergen:
    allergen = await session.get(Allergen, id)
    if allergen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allergen with id {id} not found",
        )

    update_data = allergen_update.model_dump(exclude_unset=True)
    if "name" in update_data:
        stmt = select(Allergen).where(
            Allergen.name == update_data["name"],
            Allergen.id != id,
        )
        existing_allergen = await session.scalar(stmt)
        if existing_allergen is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Allergen with name {update_data['name']} already exists",
            )

    for field_name, value in update_data.items():
        setattr(allergen, field_name, value)

    await session.commit()
    await session.refresh(allergen)
    return allergen


@router.delete("/{id}", response_model=AllergenRead)
async def allergen_delete(
    id: int,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Allergen:
    allergen = await session.get(Allergen, id)
    if allergen is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allergen with id {id} not found",
        )

    await session.delete(allergen)
    await session.commit()
    return allergen
