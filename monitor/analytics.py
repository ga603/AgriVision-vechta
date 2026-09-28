import numpy as np
from sklearn.ensemble import IsolationForest

def calculate_ndvi(red_band, nir_band):
    """
    Calculate the Normalized Difference Vegetation Index (NDVI).
    Values range from -1.0 to 1.0. Healthy crops typically score > 0.6.
    """
    # Suppress divide-by-zero warnings for pixels with zero reflection (e.g., water/shadows)
    np.seterr(divide='ignore', invalid='ignore')
    
    # NDVI Formula: (NIR - Red) / (NIR + Red)
    ndvi = (nir_band - red_band) / (nir_band + red_band)
    
    # Convert any NaN values (resulting from 0/0 division) to 0.0
    ndvi = np.nan_to_num(ndvi, nan=0.0)
    
    return ndvi

def detect_stress_anomalies(ndvi_array, contamination=0.1):
    """
    Uses an Isolation Forest algorithm to detect anomalous pixels.
    'contamination' defines the percentage of the field we expect to be under stress (10%).
    """
    # Get the dimensions of our 2D pixel grid
    rows, cols = ndvi_array.shape
    
    # Isolation Forest requires a 2D array of features, so we flatten our grid into a single column
    flat_ndvi = ndvi_array.flatten().reshape(-1, 1)
    
    # Initialize the AI model
    # random_state=42 ensures our prototype produces consistent, reproducible results
    model = IsolationForest(contamination=contamination, random_state=42)
    model.fit(flat_ndvi)
    
    # Predict anomalies: Returns 1 for normal, -1 for anomaly
    predictions = model.predict(flat_ndvi)
    
    # Reshape the 1D predictions back into the original 2D map geometry
    anomaly_map = predictions.reshape(rows, cols)
    
    # Isolation Forest finds *any* statistical outlier (both unusually high and low).
    # Since we only care about crop stress, we filter for anomalies that are strictly 
    # below the field's median NDVI.
    median_ndvi = np.median(ndvi_array)
    stressed_pixels = (anomaly_map == -1) & (ndvi_array < median_ndvi)
    
    return stressed_pixels