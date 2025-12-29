from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[2]


def show_survey_app():
    """Render the survey open-ended responses view."""
    df = pd.read_csv(BASE_DIR / "output.csv")

    open_ended_cols = [col for col in df.columns if "Open-Ended Response" in col]

    library_branch = st.sidebar.selectbox(
        "Select Library Branch",
        sorted(df["Library_Response_Changes"].dropna().unique()),
    )

    filtered_df = df[df["Library_Response_Changes"] == library_branch]

    st.title(f"Open-Ended Responses for {library_branch}")

    for col in open_ended_cols:
        st.subheader(f"**{col}**")
        responses = filtered_df[col].dropna().tolist()
        if responses:
            st.markdown("\n".join([f"- {response}" for response in responses]))
        else:
            st.markdown("- No responses")
