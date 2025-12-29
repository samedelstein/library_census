from pathlib import Path

import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[2]


@st.cache_resource
def load_shapefile(path):
    gdf = gpd.read_file(path)
    gdf["geometry"] = gdf["geometry"].apply(
        lambda geom: geom if geom.is_valid else geom.buffer(0)
    )
    return gdf


@st.cache_data
def load_census_data(path):
    df = pd.read_csv(path)
    for column in df.columns:
        if "percentage" in column:
            df[column] = (df[column] * 100).round(2)
    return df


def process_census_tracts(shapefile_path, census_data_path, county_code):
    gdf_census_tracts = load_shapefile(shapefile_path)
    gdf_census_tracts_county = gdf_census_tracts[
        gdf_census_tracts["COUNTYFP"] == county_code
    ].copy()
    gdf_census_tracts_county["TRACTCE"] = (
        gdf_census_tracts_county["TRACTCE"].astype(str).str.zfill(6)
    )
    census_df = load_census_data(census_data_path)
    gdf_census_tracts_all = gdf_census_tracts_county.merge(
        census_df, left_on="GEOIDFQ", right_on="GEO_ID", how="left"
    )
    return gdf_census_tracts_all, census_df


def show_library_census_app():
    """Render the library census data view."""
    census_tracts_shapefile_path = (
        BASE_DIR / "tl_2023_36_tract" / "tl_2023_36_tract.shp"
    )
    census_data_path = BASE_DIR / "merged_df_year.csv"

    gdf_census_tracts_onondaga_all, census_df = process_census_tracts(
        census_tracts_shapefile_path, census_data_path, "067"
    )
    gdf_census_tracts_onondaga_2022 = gdf_census_tracts_onondaga_all[
        gdf_census_tracts_onondaga_all["Year"] == 2022
    ]

    selected_column_options = census_df.filter(like="percentage").columns

    st.sidebar.title("Census Data Metrics")
    selected_column = st.sidebar.selectbox(
        "Select a value to color the census tracts:", selected_column_options
    )

    dropdown_list = [
        f"{col}: {col.replace('_', ' ').capitalize()}" for col in selected_column_options
    ]
    st.sidebar.markdown("Data based on the 2022 ACS 5-year Survey")
    st.sidebar.markdown("\n".join([f"- {i}" for i in dropdown_list]))

    geojson = gdf_census_tracts_onondaga_2022.__geo_interface__

    libraries_df = pd.read_csv(BASE_DIR / "onondaga_county_public_libraries.csv")
    libraries_gdf = gpd.GeoDataFrame(
        libraries_df,
        geometry=gpd.points_from_xy(libraries_df["Longitude"], libraries_df["Latitude"]),
        crs="EPSG:4326",
    )

    libraries_with_tracts = gpd.sjoin(
        libraries_gdf, gdf_census_tracts_onondaga_2022, how="left", op="within"
    )

    libraries_with_tracts_all = gpd.sjoin(
        libraries_gdf, gdf_census_tracts_onondaga_all, how="left", op="within"
    )

    fig = go.Figure()

    fig.add_trace(
        go.Choroplethmapbox(
            geojson=geojson,
            locations=gdf_census_tracts_onondaga_2022["GEOIDFQ"],
            z=gdf_census_tracts_onondaga_2022[selected_column],
            featureidkey="properties.GEOIDFQ",
            colorscale="RdYlGn",
            marker_opacity=0.5,
            marker_line_width=0,
            text=gdf_census_tracts_onondaga_2022["NAMELSAD"],
            hoverinfo="location+z+text",
            hovertemplate="<b>%{text}</b><br>Value: %{z}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scattermapbox(
            lat=libraries_with_tracts["Latitude"],
            lon=libraries_with_tracts["Longitude"],
            mode="markers",
            marker=go.scattermapbox.Marker(size=9, color="red"),
            text=libraries_with_tracts.apply(
                lambda row: f"{row['Library Name']}<br>{row[selected_column]:.2f}",
                axis=1,
            ),
            hoverinfo="text",
        )
    )

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=10,
        mapbox_center={"lat": 43.0481, "lon": -76.1513},
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )

    st.title("Onondaga County Public Libraries and Census Tracts Map")
    st.write(
        "This site is intended to give context about the communities each library in "
        "Onondaga County serves. Using data from the Census Bureau's American Community "
        "Survey and combining that with locations of all libraries in the County, we can "
        "get a sense for the challenges and opportunities in each location."
    )
    st.plotly_chart(fig)

    st.subheader("Census Tract and Library Data")

    libraries_with_tracts = libraries_with_tracts[
        [
            "Library Name",
            "Address",
            "City",
            "State",
            "Zip Code",
            "NAMELSAD",
        ]
        + selected_column_options.tolist()
    ]
    columns_order = [selected_column] + [
        col for col in libraries_with_tracts.columns if col not in [selected_column, "geometry"]
    ]
    combined_df = libraries_with_tracts[columns_order].sort_values(
        by=selected_column, ascending=False
    )
    st.write(combined_df)
    st.download_button(
        label="Download Data as CSV",
        data=combined_df.to_csv().encode("utf-8"),
        file_name="census_library_data.csv",
        mime="text/csv",
    )

    fig = px.line(
        libraries_with_tracts_all,
        x="Year",
        y=[selected_column],
        color="Library Name",
        title=f"Census Data Over Time by {selected_column} and Library Name",
        color_discrete_sequence=px.colors.qualitative.Plotly,
    )
    max_index = libraries_with_tracts[selected_column].idxmax()
    min_index = libraries_with_tracts[selected_column].idxmin()

    library_name_with_max_value = libraries_with_tracts.loc[max_index, "Library Name"]
    library_name_with_min_value = libraries_with_tracts.loc[min_index, "Library Name"]

    for trace in fig.data:
        if trace.name not in [library_name_with_max_value, library_name_with_min_value]:
            trace.visible = "legendonly"

    st.plotly_chart(fig)
    st.write(
        "The chart above shows change over time by library branch. By default it shows "
        "the branch with the highest and lowest values in 2022, but you can select other "
        "branches by clicking on their name to display on the chart."
    )
