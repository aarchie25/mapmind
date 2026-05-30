import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def extract_query_info(user_question: str) -> dict:
    """
    Takes a plain English question from the user.
    Returns a dictionary with location, category, and radius.
    """

    prompt = f"""You are a location extraction system. Extract information from this exact query.

USER QUERY: "{user_question}"

Rules:
1. Extract the EXACT location mentioned in the query — do not invent or assume a location
2. Extract the place category (restaurant, cafe, hospital, pharmacy, bank, park, etc.)
3. Extract the radius in km — if not mentioned use 2.0
4. If no location is mentioned, use "Tempe, Arizona, USA"
5. Always expand city names to their full form with country
6. For Indian cities, always include state and country

Respond ONLY with this exact JSON format, no extra text, no markdown:
{{"location": "full location name with country", "category": "place type", "radius_km": number}}

Examples:
Query: "restaurants in Phoenix Arizona within 3km"
Output: {{"location": "Phoenix, Arizona, USA", "category": "restaurant", "radius_km": 3.0}}

Query: "cafes near Tempe within 2km"
Output: {{"location": "Tempe, Arizona, USA", "category": "cafe", "radius_km": 2.0}}

Query: "hospitals near ASU within 1km"
Output: {{"location": "Arizona State University, Tempe, Arizona, USA", "category": "hospital", "radius_km": 1.0}}

Query: "cafes in goa"
Output: {{"location": "Panaji, Goa, India", "category": "cafe", "radius_km": 2.0}}

Query: "restaurants in mumbai"
Output: {{"location": "Mumbai, Maharashtra, India", "category": "restaurant", "radius_km": 2.0}}

Query: "hospitals in delhi"
Output: {{"location": "New Delhi, Delhi, India", "category": "hospital", "radius_km": 3.0}}

Query: "cafes in london"
Output: {{"location": "London, England, UK", "category": "cafe", "radius_km": 2.0}}

Query: "restaurants in paris"
Output: {{"location": "Paris, Ile-de-France, France", "category": "restaurant", "radius_km": 2.0}}

Query: "cafes in los angeles"
Output: {{"location": "Los Angeles, California, USA", "category": "cafe", "radius_km": 2.0}}

Query: "find cafes near me"
Output: {{"location": "Tempe, Arizona, USA", "category": "cafe", "radius_km": 2.0}}

Now extract from: "{user_question}"
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.0
    )

    result_text = response.choices[0].message.content.strip()
    print(f"LLM raw response: {result_text}")

    # Clean response in case model adds markdown backticks
    result_text = result_text.replace("```json", "").replace("```", "").strip()

    result = json.loads(result_text)
    return result
