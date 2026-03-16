from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import IngredientCreate, IngredientRead, IngredientUpdate, RecipeRead
from models import Ingredient, Recipe, RecipeIngredient, db_helper

from .recipes import get_recipe_read_data


router = APIRouter(
    tags=["Ingredients"],
    prefix="/ingredients",
)


@router.post("", response_model=IngredientRead, status_code=status.HTTP_201_CREATED)
async def ingredient_create(
    ingredient_create: IngredientCreate,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Ingredient:
    stmt = select(Ingredient).where(Ingredient.name == ingredient_create.name)
    existing_ingredient = await session.scalar(stmt)
    if existing_ingredient is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ingredient with name {ingredient_create.name} already exists",
        )

    ingredient = Ingredient(name=ingredient_create.name)
    session.add(ingredient)
    await session.commit()
    await session.refresh(ingredient)
    return ingredient


@router.get("", response_model=list[IngredientRead])
async def ingredient_list(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> list[Ingredient]:
    stmt = select(Ingredient).order_by(Ingredient.id)
    ingredients = await session.scalars(stmt)
    return ingredients.all()


@router.get("/{id}/recipes", response_model=list[RecipeRead])
async def ingredient_recipe_list(
    id: int,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> list[dict]:
    ingredient = await session.get(Ingredient, id)
    if ingredient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredient with id {id} not found",
        )

    stmt = (
        select(Recipe)
        .join(RecipeIngredient, RecipeIngredient.recipe_id == Recipe.id)
        .where(RecipeIngredient.ingredient_id == id)
        .order_by(Recipe.id)
        .distinct()
    )
    recipes = await session.scalars(stmt)
    return [
        await get_recipe_read_data(
            session=session,
            recipe=recipe,
        )
        for recipe in recipes.all()
    ]


@router.get("/{id}", response_model=IngredientRead)
async def ingredient_read_one(
    id: int,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Ingredient:
    ingredient = await session.get(Ingredient, id)
    if ingredient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredient with id {id} not found",
        )
    return ingredient


@router.put("/{id}", response_model=IngredientRead)
async def ingredient_update(
    id: int,
    ingredient_update: IngredientUpdate,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Ingredient:
    ingredient = await session.get(Ingredient, id)
    if ingredient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredient with id {id} not found",
        )

    update_data = ingredient_update.model_dump(exclude_unset=True)
    if "name" in update_data:
        stmt = select(Ingredient).where(
            Ingredient.name == update_data["name"],
            Ingredient.id != id,
        )
        existing_ingredient = await session.scalar(stmt)
        if existing_ingredient is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ingredient with name {update_data['name']} already exists",
            )

    for field_name, value in update_data.items():
        setattr(ingredient, field_name, value)

    await session.commit()
    await session.refresh(ingredient)
    return ingredient


@router.delete("/{id}", response_model=IngredientRead)
async def ingredient_delete(
    id: int,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Ingredient:
    ingredient = await session.get(Ingredient, id)
    if ingredient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredient with id {id} not found",
        )

    await session.delete(ingredient)
    await session.commit()
    return ingredient
