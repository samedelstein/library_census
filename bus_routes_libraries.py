import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from zipfile import ZipFile
import streamlit.components.v1 as components

# Extract the bus routes shapefile from the zip file
with ZipFile('CentroRoutes.zip', 'r') as zip_ref:
    zip_ref.extractall('CentroRoutes')

# Read the bus routes shapefile
bus_routes_gdf = gpd.read_file('CentroRoutes/Ono_Os_Ca_One_CentroRoutes_20150302.shp')

# Drop rows with missing geometries
bus_routes_gdf = bus_routes_gdf.dropna(subset=['geometry'])

# Ensure the CRS is in EPSG:4326
if bus_routes_gdf.crs != 'EPSG:4326':
    bus_routes_gdf = bus_routes_gdf.to_crs('EPSG:4326')

# Convert GeoDataFrame to GeoJSON with the correct structure
bus_routes_geojson = bus_routes_gdf.to_json()

# Read the libraries CSV file and create a GeoDataFrame
libraries_df = pd.read_csv("onondaga_county_public_libraries.csv")
libraries_gdf = gpd.GeoDataFrame(
    libraries_df, 
    geometry=gpd.points_from_xy(libraries_df['Longitude'], libraries_df['Latitude']),
    crs="EPSG:4326"
)

# Drop rows with missing geometries
libraries_gdf = libraries_gdf.dropna(subset=['geometry'])

# Create a Streamlit map
st.title("Libraries and Bus Routes in Onondaga County")

# Initialize a folium map centered around Onondaga County
m = folium.Map(location=[libraries_gdf.geometry.y.mean(), libraries_gdf.geometry.x.mean()], zoom_start=12)

# Add bus routes to the map using the 'LineName' field for the tooltip
folium.GeoJson(
    bus_routes_geojson,
    name="Bus Route",
    style_function=lambda x: {'color': 'blue', 'weight': 2, 'opacity': 0.5},
    tooltip=folium.GeoJsonTooltip(fields=['LineName'], aliases=['Route:'])
).add_to(m)

# Add libraries to the map
for _, row in libraries_gdf.iterrows():
    folium.Marker([row.geometry.y, row.geometry.x], popup=row['Library Name']).add_to(m)

# Display the map in Streamlit
components.html(m._repr_html_(), height=700)
