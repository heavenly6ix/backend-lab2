from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
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


def build_recipe_read(
    recipe: Recipe,
    cuisine: Cuisine,
    allergens: list[Allergen],
    ingredients: list[dict],
) -> dict:
    return {
        "id": recipe.id,
        "title": recipe.title,
        "description": recipe.description,
        "cooking_time": recipe.cooking_time,
        "difficulty": recipe.difficulty,
        "cuisine": {
            "id": cuisine.id,
            "name": cuisine.name,
        },
        "allergens": [
            {
                "id": allergen.id,
                "name": allergen.name,
            }
            for allergen in allergens
        ],
        "ingredients": ingredients,
    }


async def get_recipe_read_data(
    session: AsyncSession,
    recipe: Recipe,
) -> dict:
    # Отдельный запрос на кухню
    cuisine = await session.get(Cuisine, recipe.cuisine_id)
    if cuisine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cuisine with id {recipe.cuisine_id} not found",
        )

    #Отдельный запрос на аллергены
    allergens_stmt = (
        select(Allergen)
        .join(recipe_allergens, recipe_allergens.c.allergen_id == Allergen.id)
        .where(recipe_allergens.c.recipe_id == recipe.id)
        .order_by(Allergen.id)
    )
    allergens_result = await session.scalars(allergens_stmt)
    allergens = allergens_result.all()

    # Отдельный запрос на ингредиенты
    ingredients_stmt = (
        select(Ingredient, RecipeIngredient)
        .join(RecipeIngredient, RecipeIngredient.ingredient_id == Ingredient.id)
        .where(RecipeIngredient.recipe_id == recipe.id)
        .order_by(RecipeIngredient.id)
    )
    ingredients_result = await session.execute(ingredients_stmt)
    ingredients = [
        {
            "id": ingredient.id,
            "name": ingredient.name,
            "quantity": recipe_ingredient.quantity,
            "measurement": recipe_ingredient.measurement,
        }
        for ingredient, recipe_ingredient in ingredients_result.all()
    ]

    return build_recipe_read(
        recipe=recipe,
        cuisine=cuisine,
        allergens=allergens,
        ingredients=ingredients,
    )


@router.post("", response_model=RecipeRead, status_code=status.HTTP_201_CREATED)
async def recipe_create(
    recipe_create: RecipeCreate,
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
) -> dict:
    cuisine = await session.get(Cuisine, recipe_create.cuisine_id)
    if cuisine is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cuisine with id {recipe_create.cuisine_id} not found",
        )

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

    recipe = Recipe(
        title=recipe_create.title,
        description=recipe_create.description,
        cooking_time=recipe_create.cooking_time,
        difficulty=recipe_create.difficulty,
        cuisine_id=recipe_create.cuisine_id,
    )
    session.add(recipe)
    await session.flush()

    if allergen_ids:
        await session.execute(
            recipe_allergens.insert(),
            [
                {
                    "recipe_id": recipe.id,
                    "allergen_id": allergen_id,
                }
                for allergen_id in allergen_ids
            ],
        )

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
    await session.refresh(recipe)
    return build_recipe_read(
        recipe=recipe,
        cuisine=cuisine,
        allergens=allergens,
        ingredients=recipe_ingredients_read,
    )

# На всякий случай
# @router.get("", response_model=list[RecipeRead])
# async def recipe_list(
#     session: Annotated[
#         AsyncSession,
#         Depends(db_helper.session_getter),
#     ],
# ) -> list[dict]:
#     stmt = select(Recipe).order_by(Recipe.id)
#     recipes = await session.scalars(stmt)
#     return [
#         await get_recipe_read_data(
#             session=session,
#             recipe=recipe,
#         )
#         for recipe in recipes.all()
#     ]


@router.get("/{id}", response_model=RecipeRead)
async def recipe_read_one(
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
    return await get_recipe_read_data(
        session=session,
        recipe=recipe,
    )


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
