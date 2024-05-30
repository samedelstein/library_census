import conda
import os

conda_file_dir = conda.__file__
conda_dir = conda_file_dir.split('lib')[0]
proj_lib = os.path.join(os.path.join(conda_dir, 'share'), 'proj')
os.environ["PROJ_LIB"] = proj_lib

# Install requirements
import geopandas as gpd
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from shapely.geometry import MultiLineString
from shapely.ops import unary_union

# Function to load and validate the shapefile
@st.cache_resource
def load_shapefile(path):
    gdf = gpd.read_file(path)
    gdf['geometry'] = gdf['geometry'].apply(lambda geom: geom if geom.is_valid else geom.buffer(0))
    return gdf

# Function to load and validate the census data
@st.cache_data
def load_census_data(path):
    df = pd.read_csv(path)
    for column in df.columns:
        if 'percentage' in column:
            df[column] = (df[column] * 100).round(2)
    return df

# Load shapefile for census tracts
census_tracts_shapefile_path = "tl_2023_36_tract/tl_2023_36_tract.shp"
gdf_census_tracts = load_shapefile(census_tracts_shapefile_path)

# Filter to include only tracts in Onondaga County
gdf_census_tracts_onondaga = gdf_census_tracts[gdf_census_tracts['COUNTYFP'] == '067'].copy()
gdf_census_tracts_onondaga['TRACTCE'] = gdf_census_tracts_onondaga['TRACTCE'].astype(str).str.zfill(6)

# Load the census data
census_data_path = "merged_df.csv"
census_df = load_census_data(census_data_path)

# Merge the census data with the tracts GeoDataFrame
gdf_census_tracts_onondaga = gdf_census_tracts_onondaga.merge(census_df, left_on='GEOIDFQ', right_on='GEO_ID', how='left')

# Sidebar for selection
selected_column = st.sidebar.selectbox("Select a value to color the census tracts:", census_df.columns)

# Sidebar for selecting color scale

# Convert the GeoDataFrame to GeoJSON
geojson = gdf_census_tracts_onondaga.__geo_interface__

# Load and debug library data
libraries_df = pd.read_csv("onondaga_county_public_libraries.csv")
libraries_gdf = gpd.GeoDataFrame(
    libraries_df, 
    geometry=gpd.points_from_xy(libraries_df['Longitude'], libraries_df['Latitude']),
    crs="EPSG:4326"
)

# Perform a spatial join to determine which census tract each library is in
libraries_with_tracts = gpd.sjoin(libraries_gdf, gdf_census_tracts_onondaga, how='left', op='within')

# Display the merged library data

# Create Plotly Choropleth Map
fig = go.Figure()

# Add Choropleth layer with custom tooltip
fig.add_trace(go.Choroplethmapbox(
    geojson=geojson,
    locations=gdf_census_tracts_onondaga['GEOIDFQ'],
    z=gdf_census_tracts_onondaga[selected_column],
    featureidkey="properties.GEOIDFQ",
    colorscale='RdYlGn',
    marker_opacity=0.5,
    marker_line_width=0,
    text=gdf_census_tracts_onondaga['NAMELSAD'],  # Use NAMELSAD for the tooltip
    hoverinfo="location+z+text",  # Specify what to show in the tooltip
    hovertemplate="<b>%{text}</b><br>" + "Value: %{z}<extra></extra>"  # Custom tooltip template
))

# Add library markers with custom tooltip
fig.add_trace(go.Scattermapbox(
    lat=libraries_with_tracts['Latitude'],
    lon=libraries_with_tracts['Longitude'],
    mode='markers',
    marker=go.scattermapbox.Marker(
        size=9,
        color='red'
    ),
    text=libraries_with_tracts.apply(lambda row: f"{row['Library Name']}<br>{row[selected_column]:.2f}", axis=1),  # Custom tooltip
    hoverinfo='text'
))

# Set layout for the map
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=10,
    mapbox_center={"lat": 43.0481, "lon": -76.1513},
    margin={"r":0,"t":0,"l":0,"b":0}
)

# Display the map in the Streamlit app
st.title("Onondaga County Public Libraries and Census Tracts Map")
st.plotly_chart(fig)

# Display the data table under the map
st.subheader("Census Tract and Library Data")

# Prepare the data table
columns_order = [selected_column] + [col for col in libraries_with_tracts.columns if col not in [selected_column, 'geometry']]
combined_df = libraries_with_tracts[columns_order].sort_values(by=selected_column, ascending=False)
st.write(combined_df)
