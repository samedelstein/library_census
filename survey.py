import streamlit as st
import pandas as pd

# Load the dataset
file_path = 'output.csv'
df = pd.read_csv(file_path)

# Filter the columns with "Open-Ended Response" in their names
open_ended_cols = [col for col in df.columns if "Open-Ended Response" in col]

# Sidebar filter for Library branches, sorted alphabetically
library_branch = st.sidebar.selectbox(
    "Select Library Branch",
    sorted(df['Library_Response_Changes'].dropna().unique())
)

# Filter the dataframe by the selected library branch
filtered_df = df[df['Library_Response_Changes'] == library_branch]

# Display the open-ended responses
st.title(f"Open-Ended Responses for {library_branch}")

for col in open_ended_cols:
    st.subheader(f"**{col}**")
    responses = filtered_df[col].dropna().tolist()
    if responses:
        st.markdown('\n'.join([f"- {response}" for response in responses]))
    else:
        st.markdown("- No responses")
