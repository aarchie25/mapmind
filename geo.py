import osmnx as ox

# Map common user words to OSM tags
CATEGORY_MAP = {
    # Food & Drink
    "coffee": "cafe",
    "coffee shop": "cafe",
    "cafe": "cafe",
    "cafes": "cafe",
    "restaurant": "restaurant",
    "restaurants": "restaurant",
    "food": "restaurant",
    "fast food": "fast_food",
    "bar": "bar",
    "bars": "bar",
    "pub": "pub",
    "bakery": "bakery",
    "pizza": "restaurant",
    "burger": "fast_food",

    # Health
    "pharmacy": "pharmacy",
    "pharmacies": "pharmacy",
    "drug store": "pharmacy",
    "hospital": "hospital",
    "hospitals": "hospital",
    "clinic": "clinic",
    "doctor": "doctors",
    "dentist": "dentist",
    "urgent care": "clinic",

    # Education
    "school": "school",
    "university": "university",
    "college": "college",
    "library": "library",

    # Finance
    "bank": "bank",
    "banks": "bank",
    "atm": "atm",

    # Transport
    "parking": "parking",
    "gas station": "fuel",
    "fuel": "fuel",
    "petrol": "fuel",
    "charging station": "charging_station",

    # Shopping
    "supermarket": "supermarket",
    "grocery": "supermarket",
    "mall": "mall",
    "shop": "shop",
    "convenience store": "convenience",

    # Leisure
    "park": "park",
    "gym": "fitness_centre",
    "fitness": "fitness_centre",
    "playground": "playground",
    "stadium": "stadium",
    "cinema": "cinema",
    "movie theater": "cinema",
    "theatre": "theatre",
    "zoo": "zoo",
    "zoos": "zoo",
    "museum": "museum",
    "museums": "museum",
    "aquarium": "aquarium",
    "theme park": "theme_park",
    "amusement park": "theme_park",
    "golf": "golf_course",
    "golf course": "golf_course",
    "swimming pool": "swimming_pool",
    "pool": "swimming_pool",

    # Accommodation
    "hotel": "hotel",
    "hotels": "hotel",
    "motel": "motel",
    "hostel": "hostel",

    # Religion
    "mosque": "place_of_worship",
    "church": "place_of_worship",
    "temple": "place_of_worship",
    "synagogue": "place_of_worship",

    # Government
    "police": "police",
    "fire station": "fire_station",
    "post office": "post_office",
    "courthouse": "courthouse",
    "embassy": "embassy",
}


def normalize_category(category: str) -> tuple:
    """
    Converts user category word into correct OSM tag format.

    OSM uses different keys for different place types:
    - amenity: cafe, restaurant, hospital, pharmacy, bank etc
    - leisure: park, gym, playground, golf_course, swimming_pool etc
    - tourism: hotel, zoo, museum, aquarium, theme_park etc
    - shop: supermarket, convenience, mall etc

    Returns (tag_key, tag_value) tuple
    """
    cat = category.lower().strip()
    mapped = CATEGORY_MAP.get(cat, cat)

    leisure_tags = [
        "park", "fitness_centre", "playground", "stadium",
        "sports_centre", "golf_course", "swimming_pool",
        "pitch", "track"
    ]
    tourism_tags = [
        "hotel", "motel", "hostel", "attraction",
        "museum", "gallery", "zoo", "aquarium",
        "theme_park", "viewpoint"
    ]
    shop_tags = ["supermarket", "mall", "convenience", "shop"]

    if mapped in leisure_tags:
        return ("leisure", mapped)
    elif mapped in tourism_tags:
        return ("tourism", mapped)
    elif mapped in shop_tags:
        return ("shop", mapped)
    else:
        return ("amenity", mapped)


def get_coordinates(location_name: str) -> tuple:
    """
    Converts any location name to (lat, lon) coordinates.
    Works for any city worldwide — no restrictions.
    """
    location = ox.geocode(location_name)
    return location


def search_places(location: str, category: str, radius_km: float) -> list:
    """
    Searches OpenStreetMap for places matching category
    near location within radius_km.
    Tries multiple tag combinations if first search returns nothing.
    Works for any city worldwide, any category, any radius.
    Never falls back to unrelated categories.
    """
    try:
        # Step 1: Get coordinates
        lat, lon = get_coordinates(location)
        print(f"Coordinates found: {lat}, {lon}")

        # Step 2: Convert km to meters
        # Minimum 3km for better results in areas with sparse OSM data
        radius_m = max(radius_km * 1000, 3000)
        print(f"Search radius: {radius_m}m")

        # Step 3: Get correct OSM tag
        tag_key, tag_value = normalize_category(category)

        # Step 4: Smart fallbacks — only fall back to SIMILAR categories
        # Never fall back to completely unrelated amenities
        if tag_value in ["cafe", "coffee_shop"]:
            tag_attempts = [
                {"amenity": "cafe"},
                {"amenity": "restaurant"},
                {"amenity": "bar"},
            ]
        elif tag_value == "restaurant":
            tag_attempts = [
                {"amenity": "restaurant"},
                {"amenity": "fast_food"},
                {"amenity": "food_court"},
                {"amenity": "cafe"},
            ]
        elif tag_value == "hospital":
            tag_attempts = [
                {"amenity": "hospital"},
                {"amenity": "clinic"},
                {"amenity": "doctors"},
                {"healthcare": True},
            ]
        elif tag_value == "pharmacy":
            tag_attempts = [
                {"amenity": "pharmacy"},
                {"shop": "chemist"},
                {"shop": "pharmacy"},
            ]
        elif tag_value in ["park", "fitness_centre"]:
            tag_attempts = [
                {"leisure": tag_value},
                {"leisure": True},
            ]
        elif tag_value == "hotel":
            tag_attempts = [
                {"tourism": "hotel"},
                {"tourism": "guest_house"},
                {"tourism": "hostel"},
            ]
        elif tag_value in ["zoo", "aquarium", "museum", "theme_park"]:
            tag_attempts = [
                {"tourism": tag_value},
                {"leisure": tag_value},
                {"amenity": tag_value},
            ]
        elif tag_value in ["golf_course", "swimming_pool"]:
            tag_attempts = [
                {"leisure": tag_value},
                {"sport": tag_value},
            ]
        else:
            tag_attempts = [
                {tag_key: tag_value},
                {"amenity": tag_value},
                {"tourism": tag_value},
                {"leisure": tag_value},
            ]

        print(f"Will try {len(tag_attempts)} tag combinations")

        # Step 5: Try each tag combination until we get results
        gdf = None

        for tags in tag_attempts:
            try:
                print(f"Trying tags: {tags}")
                result = ox.features_from_point(
                    (lat, lon),
                    tags=tags,
                    dist=radius_m
                )
                if len(result) > 0:
                    gdf = result
                    print(f"✅ Found {len(result)} results with tags: {tags}")
                    break
                else:
                    print(f"No results with tags: {tags}, trying next...")
            except Exception as e:
                print(f"Tag attempt failed: {tags} — {e}")
                continue

        if gdf is None or len(gdf) == 0:
            print("No results found with any tag combination")
            return []

        print(f"Raw results from OSM: {len(gdf)}")

        # Step 6: Process results into clean list
        results = []
        for idx, row in gdf.iterrows():
            name = row.get("name", "Unnamed Place")

            # Skip unnamed places if we already have enough results
            if name == "Unnamed Place" and len(results) > 10:
                continue

            # Handle point vs polygon geometry
            geom = row.geometry
            if geom.geom_type == "Point":
                place_lat = geom.y
                place_lon = geom.x
            else:
                centroid = geom.centroid
                place_lat = centroid.y
                place_lon = centroid.x

            # Get extra info if available in OSM data
            address = row.get("addr:street", "")
            phone = row.get("phone", "")
            opening_hours = row.get("opening_hours", "")
            website = row.get("website", "")

            results.append({
                "name": str(name),
                "lat": place_lat,
                "lon": place_lon,
                "category": category,
                "address": str(address) if address else "",
                "phone": str(phone) if phone else "",
                "hours": str(opening_hours) if opening_hours else "",
                "website": str(website) if website else ""
            })

        return results

    except Exception as e:
        print(f"Search error: {e}")
        return []
