from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import RecipeCreate, RecipeRead, RecipeUpdate
from models import (
    Allergen,
    Cuisine,
    Ingredient,
    Recipe,
    RecipeIngredient,
    db_helper,
    recipe_allergens,
)


router = APIRouter(
    tags=["Recipes"],
    prefix="/recipes",
)

# Вспомогатльная функция для получения рецепта с загрузкой связей
async def _get_recipe_with_joins(
    session: AsyncSession,
    recipe_id: int,
) -> Recipe | None:
    result = await session.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(
            selectinload(Recipe.cuisine),
            selectinload(Recipe.allergens),
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
        )
    )
    return result.scalar_one_or_none()


@router.post("", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
async def recipe_create(
    recipe_create: RecipeCreate,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    # Тут проверяем существование кухни, если кухни не существует то выдаем ошибку
    cuisine = await session.get(Cuisine, recipe_create.cuisine_id)
    if cuisine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cuisine with id {recipe_create.cuisine_id} not found",
        )

    # Тут проверяем существование аллергенов, если аллергены не существует то выдаем ошибку
    allergen_ids = list(dict.fromkeys(recipe_create.allergen_ids))
    allergens: list[Allergen] = []
    if allergen_ids:
        stmt = select(Allergen).where(Allergen.id.in_(allergen_ids)).order_by(Allergen.id)
        allergens_result = await session.scalars(stmt)
        allergens = allergens_result.all()
        found_allergen_ids = {allergen.id for allergen in allergens}
        missing_allergen_ids = [
            allergen_id
            for allergen_id in allergen_ids
            if allergen_id not in found_allergen_ids
        ]
        if missing_allergen_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Allergen with id {missing_allergen_ids[0]} not found",
            )

    # Тоже самое, только с ингридиентами
    ingredient_ids = list(
        dict.fromkeys(
            ingredient.ingredient_id
            for ingredient in recipe_create.ingredients
        )
    )
    ingredients_by_id: dict[int, Ingredient] = {}
    if ingredient_ids:
        stmt = select(Ingredient).where(Ingredient.id.in_(ingredient_ids)).order_by(Ingredient.id)
        ingredients_result = await session.scalars(stmt)
        ingredients = ingredients_result.all()
        ingredients_by_id = {
            ingredient.id: ingredient
            for ingredient in ingredients
        }
        missing_ingredient_ids = [
            ingredient_id
            for ingredient_id in ingredient_ids
            if ingredient_id not in ingredients_by_id
        ]
        if missing_ingredient_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingredient with id {missing_ingredient_ids[0]} not found",
            )
    
    # Создание рецепта
    recipe = Recipe(
        title=recipe_create.title,
        description=recipe_create.description,
        cooking_time=recipe_create.cooking_time,
        difficulty=recipe_create.difficulty,
        cuisine_id=recipe_create.cuisine_id,
        allergens = allergens,
    )
    # Добавление в сессию
    session.add(recipe)
    await session.flush()

    recipe_ingredients: list[RecipeIngredient] = []
    recipe_ingredients_read: list[dict] = []
    for recipe_ingredient_create in recipe_create.ingredients:
        ingredient = ingredients_by_id[recipe_ingredient_create.ingredient_id]
        recipe_ingredient = RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=recipe_ingredient_create.ingredient_id,
            quantity=recipe_ingredient_create.quantity,
            measurement=recipe_ingredient_create.measurement,
        )
        recipe_ingredients.append(recipe_ingredient)
        recipe_ingredients_read.append(
            {
                "id": ingredient.id,
                "name": ingredient.name,
                "quantity": recipe_ingredient_create.quantity,
                "measurement": recipe_ingredient_create.measurement,
            }
        )

    if recipe_ingredients:
        session.add_all(recipe_ingredients)

    await session.commit()
    created_recipe = await _get_recipe_with_joins(session, recipe.id)
    if created_recipe is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Recipe was created, but could not be loaded",
        )

    return created_recipe

@router.get("", response_model=list[RecipeRead])
async def recipe_list(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    result = await session.execute(
        select(Recipe)
        .order_by(Recipe.id)
        .options(
            selectinload(Recipe.cuisine),
            selectinload(Recipe.allergens),
            selectinload(Recipe.ingredients).selectinload(RecipeIngredient.ingredient),
        )
    )
    return result.scalars().all()


@router.get("/{id}", response_model=RecipeRead)
async def recipe_read_one(
    id: int,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    recipe = await _get_recipe_with_joins(session, id)
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with id {id} not found",
        )
    return recipe


@router.put("/{id}", response_model=RecipeRead)
async def recipe_update(
    id: int,
    recipe_update: RecipeUpdate,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Recipe:
    recipe = await session.get(Recipe, id)
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with id {id} not found",
        )

    update_data = recipe_update.model_dump(exclude_unset=True, by_alias=False)
    for field_name, value in update_data.items():
        setattr(recipe, field_name, value)

    await session.commit()
    await session.refresh(recipe)
    return recipe


@router.delete("/{id}", response_model=RecipeRead)
async def recipe_delete(
    id: int,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> Recipe:
    recipe = await session.get(Recipe, id)
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with id {id} not found",
        )

    await session.delete(recipe)
    await session.commit()
    return recipe
