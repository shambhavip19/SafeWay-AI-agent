from services.geocoding import get_coordinates

cases = ["Baner Pune", "Shivajinagar Pune", "Mumbai", "Bengaluru", "Delhi"]

for location in cases:
    result = get_coordinates(location)
    print(location, "->", result)
    if not result:
        raise AssertionError(f"Geocoding failed for {location}")