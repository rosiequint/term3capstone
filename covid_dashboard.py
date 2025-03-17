import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests as rq
from datetime import datetime
from typing import Tuple, Dict
import numpy as np

# Configure page settings
st.set_page_config(
    page_title="COVID-19 Dashboard",
    page_icon="🦠",
    layout="wide"
)

# Constants
CONFIRMED_URL = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv"
DEATHS_URL = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv"

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def fetch_data(url: str) -> pd.DataFrame:
    """
    Fetch and cache COVID-19 data from CSSE GitHub
    """
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Failed to fetch data: {str(e)}")
        return None

def process_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
    """
    Process the raw dataframe to get country-wise data
    """
    # Melt the dataframe to convert dates from columns to rows
    df_melted = df.melt(
        id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'],
        var_name='Date',
        value_name='Cases'
    )
    
    # Convert date strings to datetime
    df_melted['Date'] = pd.to_datetime(df_melted['Date'])
    
    # Group by country and date
    df_country = df_melted.groupby(['Country/Region', 'Date'])['Cases'].sum().reset_index()
    
    # Get list of countries
    countries = sorted(df_country['Country/Region'].unique())
    
    return df_country, countries

def calculate_daily_cases(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate daily new cases from cumulative data
    """
    df = df.sort_values('Date')
    df['Daily'] = df.groupby('Country/Region')['Cases'].diff().fillna(0)
    return df

def main():
    st.title("🦠 COVID-19 Global Dashboard")
    st.write("Select countries and metrics to visualize COVID-19 data")

    # Fetch data
    with st.spinner("Fetching latest data..."):
        confirmed_df = fetch_data(CONFIRMED_URL)
        deaths_df = fetch_data(DEATHS_URL)

    if confirmed_df is None or deaths_df is None:
        st.error("Failed to load data. Please try again later.")
        return

    # Process data
    confirmed_country_df, countries = process_data(confirmed_df)
    deaths_country_df, _ = process_data(deaths_df)

    # Add daily cases
    confirmed_country_df = calculate_daily_cases(confirmed_country_df)
    deaths_country_df = calculate_daily_cases(deaths_country_df)

    # User inputs
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_countries = st.multiselect(
            "Select countries to compare",
            countries,
            default=["US", "India", "United Kingdom"]
        )

    with col2:
        metric_type = st.radio(
            "Select metric type",
            ["Daily", "Cumulative"],
            horizontal=True
        )

    if not selected_countries:
        st.warning("Please select at least one country to visualize data.")
        return

    # Create visualizations
    st.subheader("Cases Over Time")
    
    # Filter data for selected countries
    confirmed_filtered = confirmed_country_df[
        confirmed_country_df['Country/Region'].isin(selected_countries)
    ]
    deaths_filtered = deaths_country_df[
        deaths_country_df['Country/Region'].isin(selected_countries)
    ]

    # Create cases plot
    fig_cases = px.line(
        confirmed_filtered,
        x='Date',
        y='Daily' if metric_type == "Daily" else 'Cases',
        color='Country/Region',
        title=f"{metric_type} COVID-19 Cases by Country"
    )
    fig_cases.update_layout(
        xaxis_title="Date",
        yaxis_title="Number of Cases",
        hovermode='x unified'
    )
    st.plotly_chart(fig_cases, use_container_width=True)

    # Create deaths plot
    st.subheader("Deaths Over Time")
    fig_deaths = px.line(
        deaths_filtered,
        x='Date',
        y='Daily' if metric_type == "Daily" else 'Cases',
        color='Country/Region',
        title=f"{metric_type} COVID-19 Deaths by Country"
    )
    fig_deaths.update_layout(
        xaxis_title="Date",
        yaxis_title="Number of Deaths",
        hovermode='x unified'
    )
    st.plotly_chart(fig_deaths, use_container_width=True)

    # Display latest statistics
    st.subheader("Latest Statistics")
    
    latest_date = confirmed_filtered['Date'].max()
    stats_cols = st.columns(len(selected_countries))
    
    for i, country in enumerate(selected_countries):
        with stats_cols[i]:
            st.metric(
                country,
                f"Cases: {confirmed_filtered[confirmed_filtered['Country/Region'] == country]['Cases'].iloc[-1]:,.0f}",
                f"Deaths: {deaths_filtered[deaths_filtered['Country/Region'] == country]['Cases'].iloc[-1]:,.0f}"
            )

if __name__ == "__main__":
    main()
