import httpx
import logging
import urllib.parse
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Cache of coordinates for common testing queries in India (Pune, Bangalore, Mumbai, Delhi)
# This avoids hitting Nominatim API rate limits during quick iterations/tests.
LOCAL_GEOCODE_CACHE = {
    "baner, pune": {"latitude": 18.5590, "longitude": 73.7925, "display_name": "Baner, Pune, Maharashtra, India"},
    "baner pune": {"latitude": 18.5590, "longitude": 73.7925, "display_name": "Baner, Pune, Maharashtra, India"},
    "shivajinagar, pune": {"latitude": 18.5312, "longitude": 73.8445, "display_name": "Shivajinagar, Pune, Maharashtra, India"},
    "shivajinagar pune": {"latitude": 18.5312, "longitude": 73.8445, "display_name": "Shivajinagar, Pune, Maharashtra, India"},
    "kothrud, pune": {"latitude": 18.5074, "longitude": 73.8077, "display_name": "Kothrud, Pune, Maharashtra, India"},
    "kothrud pune": {"latitude": 18.5074, "longitude": 73.8077, "display_name": "Kothrud, Pune, Maharashtra, India"},
    "swargate, pune": {"latitude": 18.5018, "longitude": 73.8636, "display_name": "Swargate, Pune, Maharashtra, India"},
    "swargate pune": {"latitude": 18.5018, "longitude": 73.8636, "display_name": "Swargate, Pune, Maharashtra, India"},
    "hadapsar, pune": {"latitude": 18.5089, "longitude": 73.9259, "display_name": "Hadapsar, Pune, Maharashtra, India"},
    "hadapsar pune": {"latitude": 18.5089, "longitude": 73.9259, "display_name": "Hadapsar, Pune, Maharashtra, India"},
    "hinjewadi, pune": {"latitude": 18.5913, "longitude": 73.7389, "display_name": "Hinjewadi, Pune, Maharashtra, India"},
    "hinjewadi pune": {"latitude": 18.5913, "longitude": 73.7389, "display_name": "Hinjewadi, Pune, Maharashtra, India"},
    "pune": {"latitude": 18.5204, "longitude": 73.8567, "display_name": "Pune, Maharashtra, India"},
    "mumbai": {"latitude": 19.0760, "longitude": 72.8777, "display_name": "Mumbai, Maharashtra, India"},
    "bangalore": {"latitude": 12.9716, "longitude": 77.5946, "display_name": "Bengaluru, Karnataka, India"},
    "bengaluru": {"latitude": 12.9716, "longitude": 77.5946, "display_name": "Bengaluru, Karnataka, India"},
    "delhi": {"latitude": 28.6139, "longitude": 77.2090, "display_name": "New Delhi, Delhi, India"},
}

def get_coordinates(location_name: str) -> Optional[Dict[str, Any]]:
    """
    Geocode a string location name into latitude and longitude coordinates.
    Tries local cache first, then calls Nominatim API.
    """
    if not location_name:
        return None

    cleaned_name = location_name.strip().lower()
    
    # Check local cache first
    if cleaned_name in LOCAL_GEOCODE_CACHE:
        logger.info(f"Geocoding cache hit for location: {location_name}")
        return LOCAL_GEOCODE_CACHE[cleaned_name]

    # Handle partial matches in cache
    for cache_key, cache_val in LOCAL_GEOCODE_CACHE.items():
        if cache_key in cleaned_name or cleaned_name in cache_key:
            logger.info(f"Geocoding cache partial hit for location: {location_name} (matched: {cache_key})")
            return cache_val

    # Call OpenStreetMap Nominatim API
    # Nominatim requires a user-agent header identifying the application
    headers = {
        "User-Agent": "SafeWay-Travel-Assistant/1.0 (contact: shambhavi@example.com)"
    }
    
    encoded_location = urllib.parse.quote(location_name)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_location}&format=json&limit=1"
    
    try:
        logger.info(f"Calling Nominatim API for location: {location_name}")
        response = httpx.get(url, headers=headers, timeout=10.0)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                result = {
                    "latitude": float(data[0]["lat"]),
                    "longitude": float(data[0]["lon"]),
                    "display_name": data[0].get("display_name", location_name)
                }
                # Dynamically cache this request
                LOCAL_GEOCODE_CACHE[cleaned_name] = result
                return result
            else:
                logger.warning(f"No coordinates found for location: {location_name}")
                return None
        else:
            logger.error(f"Nominatim API returned status code {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error calling Nominatim geocoding API for {location_name}: {e}")
        return None
