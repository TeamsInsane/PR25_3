import geopandas as gpd
import plotly.express as px
import numpy as np

def get_main_map(data, geojson_path="./data/si.json"):
    fig = px.scatter_map(
    data,
    lat="lat",
    lon="lon",
    hover_name="OpisKraja",
    color_discrete_sequence=["red"],
    zoom=7,
    center={"lat": 46.0, "lon": 14.5},
    height=800,
    title="Prometne nesreče v letu 2023 (lokacije)"
    )

    fig.update_layout(map_style="open-street-map")
    return fig