from database import create_tables, get_active_ads, add_product_campaign

create_tables()

sample_ads = [
    (
        "BloomBox Luxury Florals",
        "Artisanal Fresh Rose Bouquet",
        "Florist & Gifts",
        "Handcrafted fresh rose bouquets and floral arrangements delivered fresh daily.",
        "flowers, roses, bouquet, gardening, plants, florist, gifts, wedding",
        "$45.00",
        "https://images.unsplash.com/photo-1561181286-d3fee7d55364?auto=format&fit=crop&w=600&q=80",
        "https://example.com/flowers"
    ),
    (
        "Purrfect Play Supplies",
        "Interactive Smart Feather Cat Toy",
        "Pet Supplies",
        "Rechargeable automatic motion cat toy designed to keep your feline active.",
        "cats, kittens, cat toys, pet supplies, felines, animals",
        "$19.99",
        "https://images.unsplash.com/photo-1545249390-6bdfa286032f?auto=format&fit=crop&w=600&q=80",
        "https://example.com/cat-products"
    ),
    (
        "ChocoArtisanal Treats",
        "Belgian Dark Chocolate Truffles Box",
        "Gourmet & Sweets",
        "Single-origin dark cocoa truffles handmade with organic ingredients.",
        "chocolate, cocoa, desserts, sweets, gifts, bakery, candy",
        "$24.50",
        "https://images.unsplash.com/photo-1549007994-cb92caebd54b?auto=format&fit=crop&w=600&q=80",
        "https://example.com/chocolate"
    ),
    (
        "DriveSmart Innovations",
        "Magnetic Wireless Car Dashboard Charger",
        "Automotive & Tech",
        "Fast-charging magnetic car mount compatible with all modern smartphones.",
        "cars, automobiles, driving, car accessories, vehicles, road trips",
        "$34.00",
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=600&q=80",
        "https://example.com/car-accessories"
    ),
]

existing_names = {ad.get("product_name") or ad.get("name") for ad in get_active_ads()}

for ad in sample_ads:
    if ad[1] not in existing_names:
        add_product_campaign(*ad)

print("Sample ad campaigns initialized without placeholders!")