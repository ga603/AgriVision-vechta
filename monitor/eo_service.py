import os
import numpy as np
from dotenv import load_dotenv
from sentinelhub import (
    SHConfig, 
    SentinelHubRequest, 
    DataCollection, 
    BBox, 
    CRS, 
    bbox_to_dimensions,
    MimeType
)

# Load the hidden variables from your .env file
load_dotenv()

def get_sentinel_config():
    config = SHConfig()
    
    # Securely fetch keys from the environment
    config.sh_client_id = os.getenv('CDSE_CLIENT_ID') 
    config.sh_client_secret = os.getenv('CDSE_CLIENT_SECRET')
    
    config.sh_token_url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
    config.sh_base_url = 'https://sh.dataspace.copernicus.eu'
    return config

def fetch_multispectral_data(bbox_coords, time_interval):
    """
    bbox_coords: tuple of (min_x, min_y, max_x, max_y) in WGS84
    time_interval: tuple of ('YYYY-MM-DD', 'YYYY-MM-DD')
    """
    config = get_sentinel_config()
    field_bbox = BBox(bbox=bbox_coords, crs=CRS.WGS84)
    size = bbox_to_dimensions(field_bbox, resolution=10)

    evalscript = """
    //VERSION=3
    function setup() {
        return {
            input: ["B04", "B08", "dataMask"],
            output: { bands: 3, sampleType: "FLOAT32" }
        };
    }
    function evaluatePixel(sample) {
        return [sample.B04, sample.B08, sample.dataMask];
    }
    """

    # --------------------------------------------------------------------
    # THE FIX: Explicitly define the CDSE data collection to override the
    # legacy Sentinel Hub URL hardcoded in the Python library.
    # --------------------------------------------------------------------
    CDSE_S2_L2A = DataCollection.define(
        name="CDSE_S2_L2A",
        api_id="sentinel-2-l2a",
        service_url="https://sh.dataspace.copernicus.eu"
    )
    

    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=CDSE_S2_L2A, # <--- Use the custom CDSE collection here
                time_interval=time_interval,
            )
        ],
        responses=[
            SentinelHubRequest.output_response('default', MimeType.TIFF)
        ],
        bbox=field_bbox,
        size=size,
        config=config
    )

    data = request.get_data()
    return data