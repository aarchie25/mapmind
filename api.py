from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm import extract_query_info
from geo import search_places

# Create the FastAPI application
app = FastAPI(
    title="MapMind API",
    description="Natural Language Geospatial Query System",
    version="1.0.0"
)

# Define what a request looks like
# Pydantic automatically validates incoming data


class QueryRequest(BaseModel):
    question: str  # The user's plain English question

# Define what a single place result looks like


class PlaceResult(BaseModel):
    name: str
    lat: float
    lon: float
    category: str

# Define what the full response looks like


class QueryResponse(BaseModel):
    question: str
    location: str
    category: str
    radius_km: float
    results: list[PlaceResult]
    total_found: int

# Health check endpoint
# Always useful to have — confirms the server is running - decorator


@app.get("/")
def root():
    return {"status": "MapMind API is running!"}

# Main query endpoint
# This is what Streamlit calls when user asks a question


@app.post("/query", response_model=QueryResponse)
def query_places(request: QueryRequest):
    """
    Takes a natural language question.
    Returns matching places from OpenStreetMap.


    """

    try:
        # Print statements appear when you run the app in the terminal-logs
        #  Use LLaMA3 to understand the question
        print(f"Processing question: {request.question}")
        query_info = extract_query_info(request.question)

        print(f"AI extracted: {query_info}")

        #  Search OpenStreetMap with extracted info
        places = search_places(
            location=query_info["location"],
            category=query_info["category"],
            radius_km=query_info["radius_km"]
        )

        print(f"Found {len(places)} places")

        #  Build and return the response
        return QueryResponse(
            question=request.question,
            location=query_info["location"],
            category=query_info["category"],
            radius_km=query_info["radius_km"],
            results=places,
            total_found=len(places)
        )

    except Exception as e:
        # If anything goes wrong, return a proper HTTP error
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )
