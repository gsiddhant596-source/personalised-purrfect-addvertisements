import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "adsense_ai.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():
    connection = get_connection()

    # User search tracking
    connection.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Company & Product Advertising Catalog
    connection.execute("""
        CREATE TABLE IF NOT EXISTS ad_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            target_topics TEXT NOT NULL,
            price TEXT,
            image_url TEXT,
            destination_url TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


def save_search(query: str):
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO search_history (query) VALUES (?)",
            (query,)
        )


def get_search_history():
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT id, query, searched_at
            FROM search_history
            ORDER BY id DESC
        """).fetchall()

        return [dict(row) for row in rows]


def add_product_campaign(
    company_name: str,
    product_name: str,
    category: str,
    description: str,
    target_topics: str,
    price: str = "Free",
    image_url: str = None,
    destination_url: str = "https://example.com"
):
    """Adds a complete company product listing."""
    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO ad_campaigns (
                company_name, product_name, category,
                description, target_topics, price,
                image_url, destination_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company_name, product_name, category,
            description, target_topics, price,
            image_url, destination_url
        ))
        connection.commit()
        return cursor.lastrowid


# Backward compatibility wrapper for old seed scripts
def add_ad_campaign(
    name,
    description,
    target_topics,
    image_url=None,
    destination_url=None
):
    add_product_campaign(
        company_name=name,
        product_name=name,
        category="General",
        description=description,
        target_topics=target_topics,
        price="",
        image_url=image_url,
        destination_url=destination_url or "https://example.com"
    )


def get_active_ads():
    with get_connection() as connection:
        rows = connection.execute("""
            SELECT * FROM ad_campaigns
            WHERE active = 1
            ORDER BY id DESC
        """).fetchall()

        ads = []
        for row in rows:
            d = dict(row)
            # Ensure extension compatibility expecting ad["name"]
            if "name" not in d or not d["name"]:
                d["name"] = f"{d.get('product_name', '')} by {d.get('company_name', '')}"
            ads.append(d)
        return ads