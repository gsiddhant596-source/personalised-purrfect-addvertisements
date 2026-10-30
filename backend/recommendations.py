import time
from sentence_transformers import SentenceTransformer, util
from database import get_active_ads
from sd_generator import generate_local_sd_banner

model = SentenceTransformer("all-MiniLM-L6-v2")

cached_ads = []
cached_embeddings = None
last_cache_refresh = 0
CACHE_TTL_SECONDS = 30


def refresh_ad_cache():
    global cached_ads, cached_embeddings, last_cache_refresh
    cached_ads = get_active_ads()

    if not cached_ads:
        cached_embeddings = None
        last_cache_refresh = time.time()
        return

    ad_texts = []
    for ad in cached_ads:
        topics = ad.get("target_topics", "")
        if isinstance(topics, list):
            topics = ", ".join(topics)

        name = ad.get("product_name") or ad.get("name", "")
        company = ad.get("company_name", "")
        category = ad.get("category", "")
        desc = ad.get("description", "")

        ad_texts.append(
            f"Product: {name} by {company}. Category: {category}. "
            f"Description: {desc}. Keywords: {topics}."
        )

    cached_embeddings = model.encode(
        ad_texts,
        convert_to_tensor=True,
        normalize_embeddings=True
    )
    last_cache_refresh = time.time()


def build_personalized_ad(ad: dict, page_text: str) -> tuple[str, str, str]:
    """
    Synthesizes tailored ad headlines, descriptions, and AI visual prompts 
    that bridge the user's active page theme with the product.
    """
    lower_page = page_text.lower()
    prod_name = ad.get("product_name") or ad.get("name", "Product")
    prod_desc = ad.get("description", "")
    prod_topics = (ad.get("target_topics") or "").lower()

    # 1. Cat browsing vs Dog product bridge
    if ("cat" in lower_page or "kitten" in lower_page) and ("dog" in prod_topics or "dog" in prod_name.lower()):
        headline = f"Love Cats? Don't Forget Your Dog — {prod_name}"
        description = f"While enjoying your favorite feline moments, keep your puppy equally happy and nourished with {prod_name}."
        sd_context = f"a playful kitten and a happy dog sitting together next to a bowl of {prod_name}"

    # 2. Dog browsing vs Cat product bridge
    elif ("dog" in lower_page or "puppy" in lower_page) and ("cat" in prod_topics or "cat" in prod_name.lower()):
        headline = f"Have Both Dogs & Cats at Home? Treat Them with {prod_name}"
        description = f"Ensure every pet in your family is cared for. Pamper your feline with {prod_name}."
        sd_context = f"a cute golden retriever and a fluffy cat sharing a cozy spot near {prod_name}"

    # 3. Coding / Tech browsing vs Lifestyle / Audio / Coffee products
    elif any(k in lower_page for k in ["python", "code", "programming", "software", "tech"]):
        headline = f"Supercharge Your Focus: {prod_name}"
        description = f"Level up your workflow and daily productivity sessions. {prod_desc}"
        sd_context = f"modern minimal tech workstation desk with neon ambient lighting and {prod_name}"

    # 4. Music / Streaming browsing
    elif any(k in lower_page for k in ["music", "song", "audio", "playlist", "lyrics"]):
        headline = f"The Soundtrack to Your Day with {prod_name}"
        description = f"Keep the vibe going strong wherever you are. {prod_desc}"
        sd_context = f"{prod_name} displayed in an artistic musical lifestyle setting"

    # 5. General intelligent fallback
    else:
        keywords = [w for w in page_text.split() if len(w) > 4][:5]
        theme = " ".join(keywords) if keywords else "Your Day"
        headline = f"Inspired by Your Interest in {theme.title()}: {prod_name}"
        description = f"The perfect match for what you are exploring right now. {prod_desc}"
        sd_context = f"{prod_name} in a premium studio commercial product setting"

    return headline, description, sd_context


def recommend_ads(page_content: str, limit: int = 1):
    global cached_ads, cached_embeddings, last_cache_refresh

    clean_content = " ".join(page_content.split())
    if not clean_content:
        return []

    if (
        cached_embeddings is None
        or time.time() - last_cache_refresh >= CACHE_TTL_SECONDS
    ):
        refresh_ad_cache()

    if not cached_ads or cached_embeddings is None:
        return []

    page_embedding = model.encode(
        clean_content[:4000],
        convert_to_tensor=True,
        normalize_embeddings=True
    )

    scores = util.cos_sim(page_embedding, cached_embeddings)[0]

    ranked_ads = []
    for index, ad in enumerate(cached_ads):
        score = float(scores[index].item())
        ranked_ads.append({
            "id": ad["id"],
            "name": ad.get("product_name") or ad.get("name", "Sponsored Product"),
            "category": ad.get("category", "General"),
            "description": ad.get("description", ""),
            "price": ad.get("price", ""),
            "target_topics": ad.get("target_topics", ""),
            "image_url": ad.get("image_url"),
            "destination_url": ad.get("destination_url"),
            "similarity": round(score, 4),
        })

    ranked_ads.sort(key=lambda ad: ad["similarity"], reverse=True)

    MIN_SIMILARITY = 0.15
    matches = [ad for ad in ranked_ads if ad["similarity"] >= MIN_SIMILARITY]
    selected_ads = matches[:limit] if matches else [ranked_ads[0]]

    # Apply personalized copywriting and contextual image generation
    for ad in selected_ads:
        p_headline, p_desc, sd_context = build_personalized_ad(ad, clean_content)
        ad["name"] = p_headline
        ad["description"] = p_desc

        # If the ad doesn't already have an uploaded image, synthesize the contextual bridge
        current_img = ad.get("image_url") or ""
        if "/static/uploads/" not in current_img:
            try:
                ad["image_url"] = generate_local_sd_banner(
                    product_name=ad["name"],
                    category=ad["category"],
                    description=ad["description"],
                    context=sd_context
                )
            except Exception as e:
                print(f"[SD Bridge Notice] Using catalog image: {e}")

    return selected_ads