import json
import numpy as np
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from .models import AgriculturalField, StressAnomaly
from .eo_service import fetch_multispectral_data
from .analytics import calculate_ndvi, detect_stress_anomalies

def dashboard(request):
    fields = AgriculturalField.objects.all()
    
    # Safely serialize the QuerySet into a JSON string for Leaflet.js
    field_data_list = []
    for field in fields:
        field_data_list.append({
            'id': field.id,
            'name': field.name,
            'boundary': field.boundary_coordinates
        })
        
    context = {
        'fields': fields,
        'fields_json': json.dumps(field_data_list)
    }
    return render(request, 'monitor/dashboard.html', context)

def analyze_field(request, field_id):
    """
    Triggered by the frontend to analyze a specific field.
    """
    field = get_object_or_404(AgriculturalField, id=field_id)
    
    # For this prototype, we will hardcode a bounding box around Vechta.
    bbox_coords = (8.2700, 52.7200, 8.2900, 52.7400) 
    time_interval = ('2026-08-28', '2026-09-28') 
    
    try:
        # 1. Fetch satellite data
        satellite_data = fetch_multispectral_data(bbox_coords, time_interval)
        latest_scan = satellite_data[0] 
        
        red_band = latest_scan[:, :, 0]
        nir_band = latest_scan[:, :, 1]
        
        # 2. Run Analytics Pipeline
        ndvi_array = calculate_ndvi(red_band, nir_band)
        stressed_pixels_mask = detect_stress_anomalies(ndvi_array)
        overall_ndvi = float(np.mean(ndvi_array))
        
        # 3. Extract Stressed Pixel Coordinates & Calculate Spatial Bounds
        stress_clusters = np.argwhere(stressed_pixels_mask == True).tolist()
        
        min_lon, min_lat, max_lon, max_lat = bbox_coords
        rows, cols = ndvi_array.shape
        
        # Calculate the degree step for each pixel
        lon_step = (max_lon - min_lon) / cols
        lat_step = (max_lat - min_lat) / rows
        
        heatmap_bounds = []
        for row, col in stress_clusters:
            # Arrays map from top-left, so row 0 is max_lat and col 0 is min_lon
            p_min_lon = min_lon + (col * lon_step)
            p_max_lon = p_min_lon + lon_step
            p_max_lat = max_lat - (row * lat_step)
            p_min_lat = p_max_lat - lat_step
            
            # Leaflet expects bounds in the format: [[lat1, lon1], [lat2, lon2]]
            heatmap_bounds.append([[p_min_lat, p_min_lon], [p_max_lat, p_max_lon]])
        
        # 4. Save to Database
        anomaly_record = StressAnomaly.objects.create(
            field=field,
            overall_ndvi=overall_ndvi,
            stress_clusters={"pixel_indices": stress_clusters}
        )
        
        return JsonResponse({
            'status': 'success',
            'anomaly_id': anomaly_record.id,
            'overall_ndvi': round(overall_ndvi, 3),
            'stressed_clusters_count': len(stress_clusters),
            'heatmap': heatmap_bounds # Send spatial data to frontend
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)