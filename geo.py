import osmnx as ox

CATEGORY_MAP = {
    "coffee": "cafe", "coffee shop": "cafe", "cafe": "cafe", "cafes": "cafe",
    "restaurant": "restaurant", "restaurants": "restaurant", "food": "restaurant",
    "fast food": "fast_food", "bar": "bar", "bars": "bar", "pub": "pub",
    "bakery": "bakery", "pizza": "restaurant", "burger": "fast_food",
    "pharmacy": "pharmacy", "pharmacies": "pharmacy", "drug store": "pharmacy",
    "hospital": "hospital", "hospitals": "hospital", "clinic": "clinic",
    "doctor": "doctors", "dentist": "dentist", "urgent care": "clinic",
    "school": "school", "university": "university", "college": "college",
    "library": "library", "bank": "bank", "banks": "bank", "atm": "atm",
    "parking": "parking", "gas station": "fuel", "fuel": "fuel", "petrol": "fuel",
    "supermarket": "supermarket", "grocery": "supermarket", "mall": "mall",
    "shop": "shop", "convenience store": "convenience",
    "park": "park", "gym": "fitness_centre", "fitness": "fitness_centre",
    "playground": "playground", "stadium": "stadium", "cinema": "cinema",
    "movie theater": "cinema", "theatre": "theatre",
    "zoo": "zoo", "zoos": "zoo", "museum": "museum", "aquarium": "aquarium",
    "theme park": "theme_park", "golf": "golf_course", "golf course": "golf_course",
    "swimming pool": "swimming_pool", "pool": "swimming_pool",
    "hotel": "hotel", "hotels": "hotel", "motel": "motel", "hostel": "hostel",
    "mosque": "place_of_worship", "church": "place_of_worship",
    "temple": "place_of_worship", "synagogue": "place_of_worship",
    "police": "police", "fire station": "fire_station",
    "post office": "post_office", "courthouse": "courthouse",
}


def normalize_category(category: str) -> tuple:
    cat = category.lower().strip()
    mapped = CATEGORY_MAP.get(cat, cat)
    leisure_tags = ["park", "fitness_centre", "playground",
                    "stadium", "sports_centre", "golf_course", "swimming_pool"]
    tourism_tags = ["hotel", "motel", "hostel", "attraction",
                    "museum", "gallery", "zoo", "aquarium", "theme_park"]
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
    location = ox.geocode(location_name)
    return location


def search_places(location: str, category: str, radius_km: float) -> list:
    try:
        lat, lon = get_coordinates(location)
        print(f"Coordinates found: {lat}, {lon}")

        radius_m = max(radius_km * 1000, 3000)
        print(f"Search radius: {radius_m}m")

        tag_key, tag_value = normalize_category(category)

        if tag_value in ["cafe", "coffee_shop"]:
            tag_attempts = [{"amenity": "cafe"}, {
                "amenity": "restaurant"}, {"amenity": "bar"}]
        elif tag_value == "restaurant":
            tag_attempts = [{"amenity": "restaurant"}, {"amenity": "fast_food"}, {
                "amenity": "food_court"}, {"amenity": "cafe"}]
        elif tag_value == "hospital":
            tag_attempts = [{"amenity": "hospital"}, {"amenity": "clinic"}, {
                "amenity": "doctors"}, {"healthcare": True}]
        elif tag_value == "pharmacy":
            tag_attempts = [{"amenity": "pharmacy"}, {
                "shop": "chemist"}, {"shop": "pharmacy"}]
        elif tag_value in ["park", "fitness_centre"]:
            tag_attempts = [{"leisure": tag_value}, {"leisure": True}]
        elif tag_value == "hotel":
            tag_attempts = [{"tourism": "hotel"}, {
                "tourism": "guest_house"}, {"tourism": "hostel"}]
        elif tag_value in ["zoo", "aquarium", "museum", "theme_park"]:
            tag_attempts = [{"tourism": tag_value}, {
                "leisure": tag_value}, {"amenity": tag_value}]
        elif tag_value in ["golf_course", "swimming_pool"]:
            tag_attempts = [{"leisure": tag_value}, {"sport": tag_value}]
        else:
            tag_attempts = [{tag_key: tag_value}, {"amenity": tag_value}, {
                "tourism": tag_value}, {"leisure": tag_value}]

        print(f"Will try {len(tag_attempts)} tag combinations")

        gdf = None
        for tags in tag_attempts:
            try:
                print(f"Trying tags: {tags}")
                result = ox.features_from_point(
                    (lat, lon), tags=tags, dist=radius_m)
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

        results = []
        for idx, row in gdf.iterrows():
            # Hard limit at 50 results for performance
            if len(results) >= 50:
                break

            name = row.get("name", "Unnamed Place")
            if name == "Unnamed Place" and len(results) > 10:
                continue

            geom = row.geometry
            if geom.geom_type == "Point":
                place_lat = geom.y
                place_lon = geom.x
            else:
                centroid = geom.centroid
                place_lat = centroid.y
                place_lon = centroid.x

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
