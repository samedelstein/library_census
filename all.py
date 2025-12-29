import streamlit as st

from app.views.bus_routes import show_bus_routes_libraries_app
from app.views.library_census import show_library_census_app
from app.views.survey import show_survey_app


def main():
    st.sidebar.title("Navigation")
    app = st.sidebar.radio(
        "Go to", ["Library Census Data", "Survey Responses", "Libraries and Bus Routes"]
    )

    if app == "Libraries and Bus Routes":
        show_bus_routes_libraries_app()
    elif app == "Survey Responses":
        show_survey_app()
    elif app == "Library Census Data":
        show_library_census_app()


if __name__ == "__main__":
    main()
