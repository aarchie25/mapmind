import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
from datetime import datetime
import math
import json

st.set_page_config(page_title="MapMind", page_icon="🗺️", layout="wide")

# ─── Header ───────────────────────────────────────────────────────────────────
st.title("🗺️ MapMind")
st.subheader("Natural Language Geospatial Query System")
st.markdown("Ask anything about places anywhere in the world — in plain English.")
st.divider()

# ─── Example Queries ──────────────────────────────────────────────────────────
st.markdown("**Try asking:**")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.info("🏥 Hospitals in Phoenix Arizona within 3km")
with col2:
    st.info("☕ Cafes in London within 2km")
with col3:
    st.info("🍕 Restaurants in Mumbai India within 3km")
with col4:
    st.info("💊 Pharmacies near ASU Tempe within 2km")

st.divider()

# ─── Session State ────────────────────────────────────────────────────────────
if "results_data" not in st.session_state:
    st.session_state.results_data = None
if "search_history" not in st.session_state:
    st.session_state.search_history = []

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🕐 Search History")
    if st.session_state.search_history:
        for i, h in enumerate(reversed(st.session_state.search_history[-5:])):
            st.markdown(f"**{i+1}.** {h['query']}")
            st.caption(
                f"📍 {h['location']} • {h['total']} results • {h['time']}")
            st.divider()
    else:
        st.caption("Your recent searches will appear here.")

    st.header("ℹ️ About MapMind")
    st.markdown("""
    MapMind converts plain English questions into geospatial queries using:
    - 🤖 **LLaMA3** via Groq for NLP
    - 🗺️ **OpenStreetMap** for global map data
    - ⚡ **FastAPI** for backend processing
    - 📊 **GeoPandas** for spatial analysis
    """)

    st.header("🏥 Healthcare Presets")
    st.caption("Click any preset to search instantly")
    presets = [
        "Pharmacies near ASU Tempe within 2km",
        "Hospitals in Phoenix Arizona within 5km",
        "Clinics in Downtown Tempe within 3km",
        "Doctors in Scottsdale Arizona within 3km",
        "Hospitals in rural Wyoming within 2km",
    ]
    for preset in presets:
        if st.button(preset, use_container_width=True):
            st.session_state.preset_query = preset

# ─── Helper Functions ─────────────────────────────────────────────────────────


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def is_healthcare_category(category: str) -> bool:
    healthcare_keywords = [
        "hospital", "hospitals", "pharmacy", "pharmacies",
        "clinic", "clinics", "doctor", "doctors", "dentist",
        "dentists", "urgent care", "healthcare", "medical",
        "health", "care", "treatment", "rehab", "nurse",
        "nursing", "therapy", "therapist", "counseling"
    ]
    return any(word in category.lower() for word in healthcare_keywords)


def get_access_score(total: int, radius_km: float) -> tuple:
    area_km2 = 3.14159 * (radius_km ** 2)
    density = total / area_km2
    if density >= 2:
        return (
            "🟢 Good Access",
            "success",
            f"This area has good healthcare coverage with {total} facilities within {radius_km}km. Residents have reasonable access to care."
        )
    elif density >= 0.5:
        return (
            "🟡 Limited Access",
            "warning",
            f"This area has limited healthcare access with only {total} facilities within {radius_km}km. Residents may face moderate barriers to care."
        )
    else:
        return (
            "🔴 Poor Access — Possible Healthcare Desert",
            "error",
            f"This area has critically poor healthcare access — only {total} facilities in {radius_km}km. This may qualify as a healthcare desert."
        )


# ─── Search Input ─────────────────────────────────────────────────────────────
default_query = st.session_state.get("preset_query", "")

col_input, col_button = st.columns([5, 1])
with col_input:
    question = st.text_input(
        label="Your Question",
        value=default_query,
        placeholder="e.g. Find cafes in Paris France within 2km",
        help="Ask in plain English — MapMind understands any city worldwide!",
        label_visibility="collapsed"
    )
with col_button:
    search_button = st.button(
        "🔍 Search", type="primary", use_container_width=True)

if "preset_query" in st.session_state:
    del st.session_state.preset_query

# ─── Search Logic ─────────────────────────────────────────────────────────────
if search_button and question:
    # Clear previous results before new search
    st.session_state.results_data = None
    with st.spinner("🧠 Understanding your question and searching the map..."):
        try:
            response = requests.post(
                "https://web-production-f7628f.up.railway.app/query",
                json={"question": question},
                timeout=60
            )
            if response.status_code == 200:
                st.session_state.results_data = response.json()
                data = st.session_state.results_data
                st.session_state.search_history.append({
                    "query": question,
                    "location": data["location"],
                    "total": data["total_found"],
                    "time": datetime.now().strftime("%H:%M")
                })
            else:
                st.error(
                    f"❌ API Error: {response.status_code} — {response.text}")

        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure FastAPI is running!")
        except requests.exceptions.Timeout:
            st.error("⏱️ Timed out — try a smaller radius.")
        except Exception as e:
            st.error(f"❌ Something went wrong: {str(e)}")

elif search_button and not question:
    st.warning("⚠️ Please enter a question first!")

# ─── Display Results ──────────────────────────────────────────────────────────
if st.session_state.results_data:
    data = st.session_state.results_data

    st.success("✅ Query processed successfully!")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📍 Location", data["location"])
    with col2:
        st.metric("🏷️ Category", data["category"])
    with col3:
        st.metric("📏 Radius", f"{data['radius_km']} km")
    with col4:
        st.metric("🔢 Results Found", data["total_found"])

    st.divider()

    total = data["total_found"]
    is_health = is_healthcare_category(data["category"])

    # ─── No Results ───────────────────────────────────────────────────────────
    if total == 0:
        if is_health:
            st.error("""
            🔴 HEALTHCARE DESERT DETECTED

            No healthcare facilities found in this area within the search radius.
            This indicates critically limited healthcare access — a significant
            barrier for patients seeking treatment.
            """)
            st.markdown(f"""
            **What this means for {data['location']}:**
            - Residents must travel far for basic healthcare
            - This is a known barrier for treatment access
            - Areas like this are actively studied in healthcare equity research

            **Try expanding the search:**
            - Increase radius to 10km or 20km
            - Search for a nearby larger city
            """)
        else:
            st.warning("⚠️ No places found.")
            st.markdown("""
            **Tips:**
            - Try a **larger radius** (5km or 10km)
            - Be more specific with location name
            - OSM data is richer in US/Europe than other regions
            """)

    # ─── Results Found ────────────────────────────────────────────────────────
    else:
        # Healthcare Access Score
        if is_health:
            level, color, msg = get_access_score(total, data["radius_km"])
            if color == "success":
                st.success(f"**Healthcare Access Score: {level}**\n\n{msg}")
            elif color == "warning":
                st.warning(f"**Healthcare Access Score: {level}**\n\n{msg}")
            else:
                st.error(f"**Healthcare Access Score: {level}**\n\n{msg}")

        # ─── Map ──────────────────────────────────────────────────────────────
        # Limit to 50 results for map performance
        display_results = data["results"][:50]
        display_total = len(display_results)

        st.subheader(f"🗺️ Map — showing {display_total} of {total} result(s)")

        center_lat = sum(p["lat"] for p in display_results) / display_total
        center_lon = sum(p["lon"] for p in display_results) / display_total

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=14,
            tiles="OpenStreetMap"
        )

        # Search radius circle
        folium.Circle(
            location=[center_lat, center_lon],
            radius=data["radius_km"] * 1000,
            color="blue",
            fill=True,
            fill_opacity=0.05,
            weight=2,
            popup="Search Area"
        ).add_to(m)

        # Center marker
        folium.Marker(
            location=[center_lat, center_lon],
            popup="Search Center",
            tooltip="Search Center",
            icon=folium.Icon(color="blue", icon="star")
        ).add_to(m)

        color_map = {
            "restaurant": "red",
            "cafe": "orange",
            "hospital": "blue",
            "pharmacy": "green",
            "bank": "purple",
            "park": "darkgreen",
            "hotel": "cadetblue",
            "school": "pink",
            "bar": "beige",
            "fuel": "lightred",
        }
        pin_color = color_map.get(data["category"], "red")

        for place in display_results:
            popup_html = f"<b>{place['name']}</b><br>📂 {place['category']}"
            if place.get("address"):
                popup_html += f"<br>🏠 {place['address']}"
            if place.get("phone"):
                popup_html += f"<br>📞 {place['phone']}"
            if place.get("hours"):
                popup_html += f"<br>🕐 {place['hours']}"
            if place.get("website"):
                popup_html += f"<br>🌐 <a href='{place['website']}' target='_blank'>Website</a>"

            folium.Marker(
                location=[place["lat"], place["lon"]],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=place["name"],
                icon=folium.Icon(color=pin_color, icon="info-sign")
            ).add_to(m)

        st_folium(m, width=1400, height=550, returned_objects=[], key="map")

        st.divider()

        # ─── Analytics Panel ──────────────────────────────────────────────────
        st.subheader("📊 Analytics")

        distances = [
            haversine(center_lat, center_lon, p["lat"], p["lon"])
            for p in display_results
        ]
        avg_distance = sum(distances) / len(distances)
        min_distance = min(distances)
        max_distance = max(distances)
        area_km2 = 3.14159 * (data["radius_km"] ** 2)
        density = total / area_km2

        acol1, acol2, acol3, acol4 = st.columns(4)
        with acol1:
            st.metric("📏 Avg Distance", f"{avg_distance:.2f} km")
        with acol2:
            st.metric("🔻 Nearest", f"{min_distance:.2f} km")
        with acol3:
            st.metric("🔺 Farthest", f"{max_distance:.2f} km")
        with acol4:
            st.metric("📊 Density", f"{density:.2f} per km²")

        st.divider()

        # ─── Download Buttons ─────────────────────────────────────────────────
        col_title, col_csv, col_geojson = st.columns([3, 1, 1])
        with col_title:
            st.subheader("📋 Results List")
        with col_csv:
            df = pd.DataFrame(data["results"])
            csv = df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"mapmind_{data['category']}_{data['location'].replace(' ', '_')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_geojson:
            geojson = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [p["lon"], p["lat"]]
                        },
                        "properties": {
                            "name": p["name"],
                            "category": p["category"],
                            "address": p.get("address", ""),
                            "phone": p.get("phone", ""),
                            "hours": p.get("hours", ""),
                            "website": p.get("website", "")
                        }
                    }
                    for p in data["results"]
                ]
            }
            st.download_button(
                label="⬇️ Download GeoJSON",
                data=json.dumps(geojson, indent=2),
                file_name=f"mapmind_{data['category']}_{data['location'].replace(' ', '_')}.geojson",
                mime="application/json",
                use_container_width=True
            )

        # ─── Results List ─────────────────────────────────────────────────────
        for i, place in enumerate(display_results, 1):
            with st.expander(f"{i}. {place['name']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(
                        f"📍 **Coordinates:** {place['lat']:.4f}, {place['lon']:.4f}")
                    if place.get("address"):
                        st.write(f"🏠 **Address:** {place['address']}")
                    if place.get("hours"):
                        st.write(f"🕐 **Hours:** {place['hours']}")
                with col2:
                    if place.get("phone"):
                        st.write(f"📞 **Phone:** {place['phone']}")
                    if place.get("website"):
                        st.write(f"🌐 **Website:** {place['website']}")
