from pathlib import Path
from zipfile import ZipFile

import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

BASE_DIR = Path(__file__).resolve().parents[2]


def show_bus_routes_libraries_app():
    """Render the bus routes and libraries map view."""
    zip_path = BASE_DIR / "CentroRoutes.zip"
    extract_dir = BASE_DIR / "CentroRoutes"
    extract_dir.mkdir(exist_ok=True)

    with ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    bus_routes_gdf = gpd.read_file(
        extract_dir / "Ono_Os_Ca_One_CentroRoutes_20150302.shp"
    )
    bus_routes_gdf = bus_routes_gdf.dropna(subset=["geometry"])

    if bus_routes_gdf.crs != "EPSG:4326":
        bus_routes_gdf = bus_routes_gdf.to_crs("EPSG:4326")

    bus_routes_geojson = bus_routes_gdf.to_json()

    libraries_df = pd.read_csv(BASE_DIR / "onondaga_county_public_libraries.csv")
    libraries_gdf = gpd.GeoDataFrame(
        libraries_df,
        geometry=gpd.points_from_xy(libraries_df["Longitude"], libraries_df["Latitude"]),
        crs="EPSG:4326",
    )
    libraries_gdf = libraries_gdf.dropna(subset=["geometry"])

    st.title("Libraries and Bus Routes in Onondaga County")

    m = folium.Map(
        location=[libraries_gdf.geometry.y.mean(), libraries_gdf.geometry.x.mean()],
        zoom_start=12,
    )

    folium.GeoJson(
        bus_routes_geojson,
        name="Bus Route",
        style_function=lambda x: {"color": "blue", "weight": 2, "opacity": 0.3},
        tooltip=folium.GeoJsonTooltip(fields=["LineName"], aliases=["Route:"]),
    ).add_to(m)

    for _, row in libraries_gdf.iterrows():
        folium.Marker([row.geometry.y, row.geometry.x], popup=row["Library Name"]).add_to(m)

    components.html(m._repr_html_(), height=700)
