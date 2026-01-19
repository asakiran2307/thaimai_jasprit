from flask import Flask, request, jsonify
import osmnx as ox
from geopy.distance import geodesic
import pandas as pd

app = Flask(__name__)

@app.route('/api/find_hospitals', methods=['POST'])
def find_hospitals_api():
    # No login required for this isolated function, but you could add API key auth
    data = request.get_json()
    location_query = data.get('query')
    lat = data.get('lat')
    lon = data.get('lon')

    if not location_query and not (lat and lon):
        return jsonify({'error': 'Location query or coordinates are required.'}), 400

    tags = {'amenity': ['hospital', 'clinic', 'doctors'], 'healthcare': 'hospital'}
    
    try:
        if lat and lon:
            facilities = ox.features_from_point((lat, lon), tags, dist=10000)
            center_point = (lat, lon)
        else:
            facilities = ox.features_from_place(location_query, tags)
            place_gdf = ox.geocode_to_gdf(location_query)
            center_point = (place_gdf.iloc[0]['lat'], place_gdf.iloc[0]['lon'])

        if facilities.empty:
            return jsonify({'facilities': []})

        facilities['distance'] = facilities.apply(
            lambda row: geodesic((row.geometry.centroid.y, row.geometry.centroid.x), center_point).km, axis=1
        )
        facilities = facilities.sort_values(by='distance').head(10)

        results = []
        for _, facility in facilities.iterrows():
            name = str(facility.get('name')) if pd.notna(facility.get('name')) else 'Unnamed Facility'
            address = f"{facility.get('addr:housenumber', '')} {facility.get('addr:street', '')}".strip()
            results.append({'name': name, 'address': address or 'Address not available', 'distance': f"{facility['distance']:.2f} km", 'lat': facility.geometry.centroid.y, 'lon': facility.geometry.centroid.x})
        
        return jsonify({'facilities': results})

    except Exception as e:
        return jsonify({'error': f"Could not find location or facilities. Error: {e}"}), 500