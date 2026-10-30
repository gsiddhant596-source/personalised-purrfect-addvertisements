import uuid
import shutil
from pathlib import Path
from typing import Optional
from urllib.parse import quote
import requests

from fastapi import FastAPI, Query, UploadFile, File, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from database import (
    create_tables,
    save_search,
    get_search_history,
    get_active_ads,
    add_product_campaign
)
from recommendations import recommend_ads
from sd_generator import generate_local_sd_banner

app = FastAPI(title="AdSense AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler to prevent UnicodeDecodeError if binary data errors occur
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"status": "error", "message": "Invalid form submission. Check fields."}
    )

STATIC_PATH = Path(__file__).parent / "static"
UPLOAD_PATH = STATIC_PATH / "uploads"
STATIC_PATH.mkdir(parents=True, exist_ok=True)
UPLOAD_PATH.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_PATH)), name="static")


@app.on_event("startup")
def startup():
    create_tables()


@app.get("/")
def home():
    return {"message": "AdSense AI backend is running!", "status": "success"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/search")
def search(topic: str = Query(..., min_length=1, max_length=200)):
    topic = topic.strip()
    if not topic:
        return {"error": "Please enter a search topic."}

    save_search(topic)
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(topic.replace(" ", "_"))

    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "AdSenseAI/1.0"})
        if response.status_code == 200:
            data = response.json()
            return {
                "topic": topic,
                "title": data.get("title", topic),
                "summary": data.get("extract", "No summary available."),
                "article_url": data.get("content_urls", {}).get("desktop", {}).get("page"),
            }
        return {
            "topic": topic,
            "title": topic,
            "summary": "No Wikipedia summary found.",
            "article_url": None,
        }
    except requests.RequestException:
        return {
            "topic": topic,
            "title": topic,
            "summary": "Information service temporarily unavailable.",
            "article_url": None,
        }


@app.get("/history")
def history():
    return {"history": get_search_history()}


@app.get("/ads")
def list_ads():
    return {"ads": get_active_ads()}


@app.post("/api/company/add-product")
async def create_product(
    company_name: str = Form(...),
    product_name: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    target_topics: str = Form(...),
    price: str = Form("Free"),
    destination_url: str = Form("https://example.com"),
    image_file: Optional[UploadFile] = File(default=None)
):
    final_image_url = ""

    # Ensure valid web URL formatting
    destination_url = destination_url.strip()
    if not destination_url.startswith(("http://", "https://")):
        destination_url = "https://" + destination_url

    # 1. Process drag-and-drop uploaded image
    if image_file and image_file.filename:
        file_ext = Path(image_file.filename).suffix.lower() or ".png"
        saved_filename = f"upload_{uuid.uuid4().hex[:10]}{file_ext}"
        saved_filepath = UPLOAD_PATH / saved_filename

        with open(saved_filepath, "wb") as buffer:
            shutil.copyfileobj(image_file.file, buffer)

        final_image_url = f"http://127.0.0.1:8000/static/uploads/{saved_filename}"

    # 2. If no image was dropped, synthesize one locally on the RTX 4050
    else:
        final_image_url = generate_local_sd_banner(
            product_name=product_name,
            category=category,
            description=description
        )

    # 3. Store in SQLite
    product_id = add_product_campaign(
        company_name=company_name,
        product_name=product_name,
        category=category,
        description=description,
        target_topics=target_topics,
        price=price,
        image_url=final_image_url,
        destination_url=destination_url
    )

    return {
        "status": "success",
        "product_id": product_id,
        "image_url": final_image_url
    }


@app.get("/recommend")
def get_recommendations(content: str = Query(..., min_length=1, max_length=10000)):
    return {"recommendations": recommend_ads(content)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000)