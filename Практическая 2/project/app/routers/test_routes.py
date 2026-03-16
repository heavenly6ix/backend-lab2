from pathlib import Path as FilePath
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Path, Query, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


class BodyDemoItem(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None


class QueryDemoParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    order_by: Literal["created_at", "updated_at"] = "created_at"
    tags: list[str] = []


class NestedDemoTag(BaseModel):
    label: str
    weight: int = Field(ge=1, le=10)


class NestedDemoPayload(BaseModel):
    title: str
    tags: list[NestedDemoTag]


class FormDemoModel(BaseModel):
    username: str
    email: str
    age: int


allowed_image_content_types = {
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp",
}
allowed_image_extensions = {".png", ".jpg", ".jpeg", ".webp"}
upload_directory = FilePath(__file__).resolve().parents[1] / "static" / "uploads"
upload_directory.mkdir(parents=True, exist_ok=True)

router = APIRouter(
    prefix="/test",
    tags=["test"],
)


@router.get("/ping")
def ping() -> dict[str, bool]:
    return {"ok": True}


@router.post("/body-demo")
def body_demo_create_item(item: BodyDemoItem) -> BodyDemoItem:
    return item


@router.get("/query-validate")
def query_validate_read_items(
    q: Annotated[str, Query(min_length=3, max_length=50)],
    limit: int | None = None,
) -> dict[str, str | int | None]:
    return {"q": q, "limit": limit}


@router.get("/path-validate/{item_id}")
def path_validate_read_item(
    item_id: Annotated[int, Path(ge=1, le=1000)],
) -> dict[str, int]:
    return {"item_id": item_id}


@router.get("/query-model")
def query_model_read_items(
    params: Annotated[QueryDemoParams, Query()],
) -> QueryDemoParams:
    return params


@router.post("/nested-model")
def nested_model_create_payload(payload: NestedDemoPayload) -> NestedDemoPayload:
    return payload


@router.post("/form-demo")
def form_demo_login(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
) -> dict[str, str]:
    return {"username": username, "password": password}


@router.post("/form-model-demo")
def form_model_demo_submit(
    form_data: Annotated[FormDemoModel, Form()],
) -> FormDemoModel:
    return form_data


@router.get("/format-response")
def format_response_get(
    format: str = Query(..., description="Response format: json or html"),
):
    if format == "json":
        return {
            "type": "json",
            "data": {
                "message": "Demo JSON response",
                "ok": True,
            },
        }
    if format == "html":
        return HTMLResponse("<h1>HTML</h1>")
    raise HTTPException(status_code=400, detail="Invalid format. Use json or html.")


@router.post("/upload-image")
async def upload_image_file(
    image: UploadFile = File(...),
) -> dict[str, str]:
    file_extension = FilePath(image.filename or "").suffix.lower()
    content_type = (image.content_type or "").lower()

    is_extension_valid = file_extension in allowed_image_extensions
    is_content_type_valid = content_type in allowed_image_content_types
    if not (is_extension_valid or is_content_type_valid):
        raise HTTPException(
            status_code=415,
            detail="Unsupported image type. Allowed: PNG, JPG/JPEG, WEBP.",
        )

    if not is_extension_valid:
        file_extension = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/webp": ".webp",
        }[content_type]

    filename = f"{uuid4().hex}{file_extension}"
    file_path = upload_directory / filename

    content = await image.read()
    with file_path.open("wb") as f:
        f.write(content)

    return {"url": f"/static/uploads/{filename}"}
