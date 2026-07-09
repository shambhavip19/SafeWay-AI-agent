import httpx
import logging
import math
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Real emergency resources in key Indian cities for instant offline testing and robust fallbacks
MOCK_EMERGENCY_DATA = [
    # Pune - Baner/Aundh/Shivajinagar
    {"name": "Baner Police Chowky", "resource_type": "Police Station", "latitude": 18.5595, "longitude": 73.7930, "address": "Baner Road, Pune", "contact_info": "020-25655335"},
    {"name": "Chaturshringi Police Station", "resource_type": "Police Station", "latitude": 18.5398, "longitude": 73.8272, "address": "Senapati Bapat Road, Pune", "contact_info": "020-25633355"},
    {"name": "Shivajinagar Police Station", "resource_type": "Police Station", "latitude": 18.5310, "longitude": 73.8435, "address": "Shivajinagar, Pune", "contact_info": "020-25536263"},
    {"name": "Jupiter Hospital", "resource_type": "Hospital", "latitude": 18.5568, "longitude": 73.7744, "address": "Baner-Balewadi Road, Pune", "contact_info": "020-27219000"},
    {"name": "Medipoint Hospital", "resource_type": "Hospital", "latitude": 18.5620, "longitude": 73.8035, "address": "New DP Road, Aundh, Pune", "contact_info": "020-67484748"},
    {"name": "Sancheti Hospital", "resource_type": "Hospital", "latitude": 18.5315, "longitude": 73.8505, "address": "Shivajinagar, Pune", "contact_info": "020-27999999"},
    {"name": "Kothrud Police Station", "resource_type": "Police Station", "latitude": 18.5061, "longitude": 73.8115, "address": "Kothrud, Pune", "contact_info": "020-25391212"},
    {"name": "Sahyadri Super Speciality Hospital", "resource_type": "Hospital", "latitude": 18.5036, "longitude": 73.8225, "address": "Kothrud, Pune", "contact_info": "020-67213000"},
    
    # Bangalore
    {"name": "Koramangala Police Station", "resource_type": "Police Station", "latitude": 12.9348, "longitude": 77.6200, "address": "Koramangala, Bengaluru", "contact_info": "080-22942571"},
    {"name": "St. John's Medical College Hospital", "resource_type": "Hospital", "latitude": 12.9334, "longitude": 77.6244, "address": "Sarjapur Road, Koramangala, Bengaluru", "contact_info": "080-22065000"},
    {"name": "Indiranagar Police Station", "resource_type": "Police Station", "latitude": 12.9784, "longitude": 77.6408, "address": "Indiranagar, Bengaluru", "contact_info": "080-22942576"},
    {"name": "Chinmaya Mission Hospital (CMH)", "resource_type": "Hospital", "latitude": 12.9778, "longitude": 77.6385, "address": "CMH Road, Indiranagar, Bengaluru", "contact_info": "080-25280461"},
    
    # Mumbai
    {"name": "Colaba Police Station", "resource_type": "Police Station", "latitude": 18.9189, "longitude": 72.8284, "address": "Colaba, Mumbai", "contact_info": "022-22856817"},
    {"name": "Bombay Hospital & Medical Research Centre", "resource_type": "Hospital", "latitude": 18.9405, "longitude": 72.8280, "address": "Marine Lines, Mumbai", "contact_info": "022-22067676"},
    
    # Delhi
    {"name": "Connaught Place Police Station", "resource_type": "Police Station", "latitude": 28.6289, "longitude": 77.2185, "address": "Connaught Place, New Delhi", "contact_info": "011-23340050"},
    {"name": "Ram Manohar Lohia Hospital", "resource_type": "Hospital", "latitude": 28.6258, "longitude": 77.2014, "address": "Baba Kharak Singh Marg, New Delhi", "contact_info": "011-23365525"}
]

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth in meters using the Haversine formula.
    """
    # Earth radius in meters
    R = 6371000.0
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
        
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    return R * c

def get_nearby_emergency_services(latitude: float, longitude: float, radius_meters: float = 3000) -> Dict[str, Any]:
    """
    Find nearby emergency resources (police, hospitals) within a given radius in meters.
    First tries Overpass API. If that fails or yields 0 results, filters mock database.
    """
    resources = []
    
    # Overpass Query
    overpass_url = "https://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json][timeout:15];
    (
      node["amenity"="police"](around:{radius_meters},{latitude},{longitude});
      way["amenity"="police"](around:{radius_meters},{latitude},{longitude});
      node["amenity"="hospital"](around:{radius_meters},{latitude},{longitude});
      way["amenity"="hospital"](around:{radius_meters},{latitude},{longitude});
    );
    out body center;
    """
    
    try:
        logger.info(f"Querying Overpass API for emergency services around ({latitude}, {longitude})")
        response = httpx.post(overpass_url, data={"data": overpass_query}, timeout=15.0)
        
        if response.status_code == 200:
            data = response.json()
            elements = data.get("elements", [])
            for elem in elements:
                # Extract lat/lon depending on node or way (way has center)
                elem_lat = elem.get("lat") or elem.get("center", {}).get("lat")
                elem_lon = elem.get("lon") or elem.get("center", {}).get("lon")
                
                if elem_lat is None or elem_lon is None:
                    continue
                
                tags = elem.get("tags", {})
                name = tags.get("name")
                amenity = tags.get("amenity")
                
                # Normalize types
                resource_type = "Police Station" if amenity == "police" else "Hospital"
                if not name:
                    name = f"Unnamed {resource_type}"
                    
                dist = haversine_distance(latitude, longitude, elem_lat, elem_lon)
                
                resources.append({
                    "name": name,
                    "resource_type": resource_type,
                    "latitude": elem_lat,
                    "longitude": elem_lon,
                    "address": tags.get("addr:full") or tags.get("addr:street", "Nearby"),
                    "contact_info": tags.get("phone") or tags.get("contact:phone", "N/A"),
                    "distance_meters": round(dist)
                })
            
            logger.info(f"Overpass API found {len(resources)} emergency services.")
    except Exception as e:
        logger.error(f"Error querying Overpass API: {e}. Falling back to preloaded database.")

    # Fallback/supplement with preloaded local database
    # Filter local mock database within radius
    local_count = 0
    for item in MOCK_EMERGENCY_DATA:
        dist = haversine_distance(latitude, longitude, item["latitude"], item["longitude"])
        if dist <= radius_meters:
            # Check if we already have it in the list (avoid duplicates by name similarity)
            if not any(res["name"].lower() == item["name"].lower() for res in resources):
                item_copy = item.copy()
                item_copy["distance_meters"] = round(dist)
                resources.append(item_copy)
                local_count += 1
                
    if local_count > 0:
        logger.info(f"Loaded {local_count} resources from local backup.")

    # Sort by distance
    resources.sort(key=lambda x: x["distance_meters"])

    # Count police and hospitals
    police_count = sum(1 for r in resources if r["resource_type"] == "Police Station")
    hospital_count = sum(1 for r in resources if r["resource_type"] == "Hospital")

    return {
        "police_count": police_count,
        "hospital_count": hospital_count,
        "resources": resources
    }
