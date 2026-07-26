import httpx
import logging
import urllib.parse
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Cache of coordinates for common testing queries in India (Pune, Bangalore, Mumbai, Delhi)
# This avoids hitting Nominatim API rate limits during quick iterations/tests.
LOCAL_GEOCODE_CACHE = {
    # Pune locations - comprehensive coverage
    "baner, pune": {"latitude": 18.5590, "longitude": 73.7925, "display_name": "Baner, Pune, Maharashtra, India"},
    "baner pune": {"latitude": 18.5590, "longitude": 73.7925, "display_name": "Baner, Pune, Maharashtra, India"},
    "baner": {"latitude": 18.5590, "longitude": 73.7925, "display_name": "Baner, Pune, Maharashtra, India"},
    "shivajinagar, pune": {"latitude": 18.5312, "longitude": 73.8445, "display_name": "Shivajinagar, Pune, Maharashtra, India"},
    "shivajinagar pune": {"latitude": 18.5312, "longitude": 73.8445, "display_name": "Shivajinagar, Pune, Maharashtra, India"},
    "shivajinagar": {"latitude": 18.5312, "longitude": 73.8445, "display_name": "Shivajinagar, Pune, Maharashtra, India"},
    "kothrud, pune": {"latitude": 18.5074, "longitude": 73.8077, "display_name": "Kothrud, Pune, Maharashtra, India"},
    "kothrud pune": {"latitude": 18.5074, "longitude": 73.8077, "display_name": "Kothrud, Pune, Maharashtra, India"},
    "kothrud": {"latitude": 18.5074, "longitude": 73.8077, "display_name": "Kothrud, Pune, Maharashtra, India"},
    "swargate, pune": {"latitude": 18.5018, "longitude": 73.8636, "display_name": "Swargate, Pune, Maharashtra, India"},
    "swargate pune": {"latitude": 18.5018, "longitude": 73.8636, "display_name": "Swargate, Pune, Maharashtra, India"},
    "swargate": {"latitude": 18.5018, "longitude": 73.8636, "display_name": "Swargate, Pune, Maharashtra, India"},
    "hadapsar, pune": {"latitude": 18.5089, "longitude": 73.9259, "display_name": "Hadapsar, Pune, Maharashtra, India"},
    "hadapsar pune": {"latitude": 18.5089, "longitude": 73.9259, "display_name": "Hadapsar, Pune, Maharashtra, India"},
    "hadapsar": {"latitude": 18.5089, "longitude": 73.9259, "display_name": "Hadapsar, Pune, Maharashtra, India"},
    "hinjewadi, pune": {"latitude": 18.5913, "longitude": 73.7389, "display_name": "Hinjewadi, Pune, Maharashtra, India"},
    "hinjewadi pune": {"latitude": 18.5913, "longitude": 73.7389, "display_name": "Hinjewadi, Pune, Maharashtra, India"},
    "hinjewadi": {"latitude": 18.5913, "longitude": 73.7389, "display_name": "Hinjewadi, Pune, Maharashtra, India"},
    "lmd chowk, pune": {"latitude": 18.5630, "longitude": 73.8086, "display_name": "LMD Chowk, Pune, Maharashtra, India"},
    "lmd chowk": {"latitude": 18.5630, "longitude": 73.8086, "display_name": "LMD Chowk, Pune, Maharashtra, India"},
    "bavdhan, pune": {"latitude": 18.5730, "longitude": 73.7900, "display_name": "Bavdhan, Pune, Maharashtra, India"},
    "bavdhan": {"latitude": 18.5730, "longitude": 73.7900, "display_name": "Bavdhan, Pune, Maharashtra, India"},
    "pune airport": {"latitude": 18.5799, "longitude": 73.9198, "display_name": "Pune Airport, Maharashtra, India"},
    "pune airport, pune": {"latitude": 18.5799, "longitude": 73.9198, "display_name": "Pune Airport, Maharashtra, India"},
    "sector 7, kharghar": {"latitude": 19.0430, "longitude": 73.1094, "display_name": "Sector 7 Kharghar, Navi Mumbai, Maharashtra, India"},
    "kharghar": {"latitude": 19.0430, "longitude": 73.1094, "display_name": "Kharghar, Navi Mumbai, Maharashtra, India"},
    "kalyani nagar, pune": {"latitude": 18.5645, "longitude": 73.9245, "display_name": "Kalyani Nagar, Pune, Maharashtra, India"},
    "kalyani nagar": {"latitude": 18.5645, "longitude": 73.9245, "display_name": "Kalyani Nagar, Pune, Maharashtra, India"},
    "market yard, pune": {"latitude": 18.5425, "longitude": 73.8635, "display_name": "Market Yard, Pune, Maharashtra, India"},
    "market yard": {"latitude": 18.5425, "longitude": 73.8635, "display_name": "Market Yard, Pune, Maharashtra, India"},
    
    # Major cities
    "pune": {"latitude": 18.5204, "longitude": 73.8567, "display_name": "Pune, Maharashtra, India"},
    "mumbai": {"latitude": 19.0760, "longitude": 72.8777, "display_name": "Mumbai, Maharashtra, India"},
    "bangalore": {"latitude": 12.9716, "longitude": 77.5946, "display_name": "Bengaluru, Karnataka, India"},
    "bengaluru": {"latitude": 12.9716, "longitude": 77.5946, "display_name": "Bengaluru, Karnataka, India"},
    "delhi": {"latitude": 28.6139, "longitude": 77.2090, "display_name": "New Delhi, Delhi, India"},
    "new delhi": {"latitude": 28.6139, "longitude": 77.2090, "display_name": "New Delhi, Delhi, India"},
    "kolkata": {"latitude": 22.5726, "longitude": 88.3639, "display_name": "Kolkata, West Bengal, India"},
    "chennai": {"latitude": 13.0827, "longitude": 80.2707, "display_name": "Chennai, Tamil Nadu, India"},
    "hyderabad": {"latitude": 17.3850, "longitude": 78.4867, "display_name": "Hyderabad, Telangana, India"},
    "jaipur": {"latitude": 26.9124, "longitude": 75.7873, "display_name": "Jaipur, Rajasthan, India"},
}

def get_coordinates(location_name: str) -> Optional[Dict[str, Any]]:
    """
    Geocode a string location name into latitude and longitude coordinates.
    Tries local cache first, then calls Nominatim API with retry logic.
    """
    if not location_name:
        return None

    cleaned_name = location_name.strip().lower()
    
    # 1. Check exact match in cache
    if cleaned_name in LOCAL_GEOCODE_CACHE:
        logger.info(f"Geocoding cache hit for location: {location_name}")
        return LOCAL_GEOCODE_CACHE[cleaned_name]

    # 2. Try variations with/without commas and state names
    variations = [cleaned_name]
    if "," in cleaned_name:
        # Try without comma: "Baner, Pune" -> "baner pune"
        variations.append(cleaned_name.replace(",", "").strip())
        # Try first part only: "Baner, Pune" -> "baner"
        variations.append(cleaned_name.split(",")[0].strip())
    else:
        # Try adding "pune" for single place names
        if "pune" not in cleaned_name and "mumbai" not in cleaned_name:
            variations.append(f"{cleaned_name}, pune")
            variations.append(f"{cleaned_name} pune")

    for var in variations:
        if var in LOCAL_GEOCODE_CACHE:
            logger.info(f"Geocoding cache hit for location: {location_name} (matched variation: {var})")
            return LOCAL_GEOCODE_CACHE[var]

    # 3. Handle partial matches in cache
    for cache_key, cache_val in LOCAL_GEOCODE_CACHE.items():
        if cache_key in cleaned_name or cleaned_name in cache_key:
            logger.info(f"Geocoding cache partial hit for location: {location_name} (matched: {cache_key})")
            return cache_val

    # 4. Call OpenStreetMap Nominatim API with retry logic
    headers = {
        "User-Agent": "SafeWay-Travel-Assistant/1.0 (contact: shambhavi@example.com)"
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            encoded_location = urllib.parse.quote(location_name)
            url = f"https://nominatim.openstreetmap.org/search?q={encoded_location}&format=json&limit=1&countrycodes=in"
            
            logger.info(f"Calling Nominatim API for location: {location_name} (attempt {attempt + 1}/{max_retries})")
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
                    # Try next variation if this attempt didn't find anything
                    if attempt < max_retries - 1:
                        time.sleep(1)  # Rate limit: wait before retry
                        continue
                    return None
            elif response.status_code == 429:  # Rate limited
                logger.warning(f"Nominatim API rate limited. Waiting before retry... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                logger.error(f"Nominatim API returned status code {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return None
        except httpx.TimeoutException:
            logger.warning(f"Nominatim API timeout. Retrying... (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return None
        except Exception as e:
            logger.error(f"Error calling Nominatim geocoding API for {location_name}: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return None
    
    logger.error(f"Failed to geocode location after {max_retries} attempts: {location_name}")
    return None
