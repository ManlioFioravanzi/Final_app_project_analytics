import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import os

st.set_page_config(
    page_title="Car Sharing Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS — Light / White theme ─────────────────────────────────────────
st.markdown("""
<style>
    /* Full white background */
    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stApp"],
    .main, .block-container {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
    }

    /* Sidebar — white, thin right border */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div:first-child {
        background-color: #ffffff !important;
        border-right: 1px solid #e0e0e0;
    }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: #f4f6fb;
        border: 1px solid #dce3f0;
        border-radius: 12px;
        padding: 18px 22px;
    }
    div[data-testid="metric-container"] label {
        color: #6b7a99 !important;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #1a1a2e !important;
        font-size: 1.7rem;
        font-weight: 700;
    }

    /* Section headers */
    .section-header {
        color: #8892a4;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 12px 0 4px 0;
    }

    /* Tabs container */
    div[data-testid="stTabs"] {
        background-color: #f0f2f8;
        border-radius: 14px;
        padding: 6px 8px;
        margin-bottom: 20px;
        border: 1px solid #e2e6f0;
    }

    /* All tab buttons */
    button[data-baseweb="tab"] {
        font-size: 1.0rem !important;
        font-weight: 600 !important;
        color: #7a88a8 !important;
        padding: 12px 28px !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
        gap: 8px !important;
    }

    /* Emoji inside tab — make it bigger */
    button[data-baseweb="tab"] p {
        font-size: 1.15rem !important;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Hover */
    button[data-baseweb="tab"]:hover {
        background-color: #e2e8f5 !important;
        color: #1a1a2e !important;
        transform: translateY(-1px) !important;
    }

    /* Active tab */
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #ffffff !important;
        color: #1a1a2e !important;
        box-shadow: 0 3px 12px rgba(67, 97, 238, 0.15) !important;
        border-bottom: 3px solid #4361ee !important;
    }

    /* Hide default underline indicator */
    div[data-testid="stTabs"] div[role="tablist"] div[data-testid="stMarkdownContainer"] {
        display: none;
    }

    /* Dividers */
    hr { border-color: #e8eaf0 !important; }

    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Data Loading ──────────────────────────────────────────────────────────────
BASE = os.path.dirname(__file__)

def _find_csv(filename):
    """Try common folder locations for the CSV files."""
    candidates = [
        os.path.join(BASE, filename),
        os.path.join(BASE, "datasets", filename),
        os.path.join(BASE, "data", filename),
        os.path.join(BASE, "Session-04-car_sharing_data_for_Streamlit", filename),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(
        f"Cannot find '{filename}'. Checked:\n" + "\n".join(candidates)
    )

@st.cache_data
def load_data():
    trips  = pd.read_csv(_find_csv("trips.csv"))
    cars   = pd.read_csv(_find_csv("cars.csv"))
    cities = pd.read_csv(_find_csv("cities.csv"))
    return trips, cars, cities

trips, cars, cities = load_data()

# ── Merge & Transform ─────────────────────────────────────────────────────────
trips_merged = trips.merge(cars, left_on="car_id", right_on="id", suffixes=("", "_car"))
trips_merged = trips_merged.merge(cities, on="city_id")
trips_merged = trips_merged.drop(
    columns=["id_car", "city_id", "customer_id", "id", "car_id"], errors="ignore"
)
trips_merged["pickup_time"]     = pd.to_datetime(trips_merged["pickup_time"])
trips_merged["dropoff_time"]    = pd.to_datetime(trips_merged["dropoff_time"])
trips_merged["pickup_date"]     = trips_merged["pickup_time"].dt.date
trips_merged["trip_duration_h"] = (
    (trips_merged["dropoff_time"] - trips_merged["pickup_time"]).dt.total_seconds() / 3600
)

# ── Sidebar Filters ───────────────────────────────────────────────────────────
st.sidebar.markdown("## 🚗 Car Sharing")
st.sidebar.markdown("---")

st.sidebar.markdown('<p class="section-header">Brand</p>', unsafe_allow_html=True)
all_brands = sorted(trips_merged["brand"].unique())
cars_brand = st.sidebar.multiselect("", options=all_brands, default=all_brands, label_visibility="collapsed")

st.sidebar.markdown('<p class="section-header">City</p>', unsafe_allow_html=True)
all_cities = sorted(trips_merged["city_name"].unique())
sel_cities = st.sidebar.multiselect("", options=all_cities, default=all_cities, label_visibility="collapsed")

st.sidebar.markdown('<p class="section-header">Date Range</p>', unsafe_allow_html=True)
min_date = trips_merged["pickup_date"].min()
max_date = trips_merged["pickup_date"].max()
date_range = st.sidebar.date_input("", value=(min_date, max_date), min_value=min_date, max_value=max_date, label_visibility="collapsed")

# Apply filters
df = trips_merged.copy()
if cars_brand:
    df = df[df["brand"].isin(cars_brand)]
if sel_cities:
    df = df[df["city_name"].isin(sel_cities)]
if len(date_range) == 2:
    df = df[(df["pickup_date"] >= date_range[0]) & (df["pickup_date"] <= date_range[1])]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🚗 Car Sharing Dashboard")
st.markdown("<span style='color:#6b7a99'>Real-time analytics across cities, brands and time periods.</span>", unsafe_allow_html=True)
st.markdown("---")

# ── KPI Metrics ───────────────────────────────────────────────────────────────
total_trips    = len(df)
total_revenue  = df["revenue"].sum()
total_distance = df["distance"].sum()
top_car        = df.groupby("model")["revenue"].sum().idxmax() if not df.empty else "—"
avg_duration   = df["trip_duration_h"].mean()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Trips",         f"{total_trips:,}")
c2.metric("Total Revenue",       f"€{total_revenue:,.0f}")
c3.metric("Total Distance (km)", f"{total_distance:,.0f}")
c4.metric("Top Model by Revenue", top_car)
c5.metric("Avg Trip Duration",   f"{avg_duration:.1f} h")

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊  Charts", "🌍  Geographic Maps", "🔎  Data Preview"])

COLORS = px.colors.qualitative.Pastel

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Charts (Plotly)
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    col_left, col_right = st.columns(2)

    with col_left:
        # Trips Over Time
        trips_ot = df.groupby("pickup_date").size().reset_index(name="Trips")
        fig1 = px.line(trips_ot, x="pickup_date", y="Trips",
                       title="Trips Over Time",
                       template="simple_white",
                       color_discrete_sequence=["#4361ee"])
        fig1.update_layout(margin=dict(t=40, b=20), height=280)
        st.plotly_chart(fig1, use_container_width=True)

        # Revenue Per Car Model
        rev_model = (df.groupby("model")["revenue"].sum()
                     .sort_values(ascending=False).reset_index())
        fig2 = px.bar(rev_model, x="model", y="revenue",
                      title="Revenue Per Car Model",
                      template="simple_white",
                      color="model", color_discrete_sequence=COLORS)
        fig2.update_layout(showlegend=False, margin=dict(t=40, b=20), height=300)
        st.plotly_chart(fig2, use_container_width=True)

        # Trips Per Car Model
        trips_model = (df.groupby("model").size()
                       .sort_values(ascending=False).reset_index(name="Trips"))
        fig3 = px.bar(trips_model, x="model", y="Trips",
                      title="Number of Trips Per Car Model",
                      template="simple_white",
                      color="model", color_discrete_sequence=COLORS)
        fig3.update_layout(showlegend=False, margin=dict(t=40, b=20), height=300)
        st.plotly_chart(fig3, use_container_width=True)

    with col_right:
        # Cumulative Revenue
        cum_rev = (df.groupby("pickup_date")["revenue"].sum()
                   .cumsum().reset_index().rename(columns={"revenue": "Cumulative Revenue"}))
        fig4 = px.area(cum_rev, x="pickup_date", y="Cumulative Revenue",
                       title="Cumulative Revenue Growth",
                       template="simple_white",
                       color_discrete_sequence=["#7209b7"])
        fig4.update_layout(margin=dict(t=40, b=20), height=280)
        st.plotly_chart(fig4, use_container_width=True)

        # Revenue by City
        rev_city = (df.groupby("city_name")["revenue"].sum()
                    .sort_values(ascending=False).reset_index())
        fig5 = px.bar(rev_city, x="city_name", y="revenue",
                      title="Revenue by City",
                      template="simple_white",
                      color="city_name", color_discrete_sequence=COLORS)
        fig5.update_layout(showlegend=False, margin=dict(t=40, b=20), height=300)
        st.plotly_chart(fig5, use_container_width=True)

        # Avg Duration by City
        avg_dur = (df.groupby("city_name")["trip_duration_h"].mean()
                   .sort_values(ascending=False).reset_index())
        fig6 = px.bar(avg_dur, x="city_name", y="trip_duration_h",
                      title="Avg Trip Duration by City (hours)",
                      template="simple_white",
                      color="city_name", color_discrete_sequence=COLORS)
        fig6.update_layout(showlegend=False, margin=dict(t=40, b=20), height=300,
                           yaxis_title="Hours")
        st.plotly_chart(fig6, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Geographic Maps
# ══════════════════════════════════════════════════════════════════════════════
with tab2:

    CARTO_LIGHT = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"

    # ── Heatmap ───────────────────────────────────────────────────────────────
    st.markdown("#### 🔥 Trip Pickup Heatmap")
    st.caption("Density of trip pickups across all locations")

    heatmap_data = df[["pickup_lat", "pickup_lon"]].dropna().rename(
        columns={"pickup_lat": "lat", "pickup_lon": "lon"}
    )
    heatmap_layer = pdk.Layer(
        "HeatmapLayer",
        data=heatmap_data,
        get_position=["lon", "lat"],
        aggregation="MEAN",
        radiusPixels=50,
        intensity=1.5,
        threshold=0.02,
        opacity=0.9,
        color_range=[
            [0, 0, 180, 0],
            [0, 120, 255, 80],
            [0, 220, 120, 140],
            [255, 230, 0, 180],
            [255, 100, 0, 220],
            [255, 0, 0, 255],
        ],
    )
    st.pydeck_chart(pdk.Deck(
        layers=[heatmap_layer],
        initial_view_state=pdk.ViewState(
            latitude=heatmap_data["lat"].mean(),
            longitude=heatmap_data["lon"].mean(),
            zoom=4, pitch=0,
        ),
        map_style=CARTO_LIGHT,
    ))

    st.markdown("---")

    # ── City Bubble Map ───────────────────────────────────────────────────────
    st.markdown("#### 🌍 Revenue & Trips by City")
    st.caption("Bubble size = total revenue · Hover for details")

    city_stats = (
        df.groupby("city_name")
        .agg(total_revenue=("revenue", "sum"), trip_count=("revenue", "count"))
        .reset_index()
    )
    city_map_df = city_stats.merge(cities[["city_name", "city_lat", "city_long"]], on="city_name")
    city_map_df["radius"] = (city_map_df["total_revenue"] / city_map_df["total_revenue"].max() * 80000).clip(lower=5000)
    max_trips = city_map_df["trip_count"].max()
    city_map_df["color_r"] = (255 * city_map_df["trip_count"] / max_trips).astype(int)
    city_map_df["color_g"] = (80 * (1 - city_map_df["trip_count"] / max_trips)).astype(int)
    city_map_df["color_b"] = 200

    st.pydeck_chart(pdk.Deck(
        layers=[
            pdk.Layer("ScatterplotLayer", data=city_map_df,
                      get_position=["city_long", "city_lat"],
                      get_radius="radius",
                      get_fill_color=["color_r", "color_g", "color_b", 180],
                      get_line_color=[255, 255, 255, 120],
                      stroked=True, line_width_min_pixels=1, pickable=True),
            pdk.Layer("TextLayer", data=city_map_df,
                      get_position=["city_long", "city_lat"],
                      get_text="city_name",
                      get_size=14, get_color=[255, 255, 255, 220],
                      get_alignment_baseline="'bottom'", get_anchor="'middle'"),
        ],
        initial_view_state=pdk.ViewState(
            latitude=city_map_df["city_lat"].mean(),
            longitude=city_map_df["city_long"].mean(),
            zoom=3.5, pitch=30,
        ),
        map_style=CARTO_LIGHT,
        tooltip={
            "html": "<b>{city_name}</b><br/>Revenue: €{total_revenue}<br/>Trips: {trip_count}",
            "style": {"backgroundColor": "#1e2130", "color": "#ffffff"},
        },
    ))

    st.markdown("---")

    # ── Arc Map ───────────────────────────────────────────────────────────────
    st.markdown("#### ✈️ Trip Routes (Arc Map)")

    # Pick city with most trips, use exact city coords for reliable centering
    top_city_name = df["city_name"].value_counts().idxmax()
    arc_city_df = df[df["city_name"] == top_city_name]
    arc_sample = arc_city_df[["pickup_lat", "pickup_lon", "dropoff_lat", "dropoff_lon"]].dropna().sample(
        n=min(300, len(arc_city_df)), random_state=42
    )
    city_row = cities[cities["city_name"] == top_city_name].iloc[0]
    center_lat = float(city_row["city_lat"])
    center_lon = float(city_row["city_long"])

    st.caption(f"300 trips in **{top_city_name}** — blue = pickup · red = dropoff")

    st.pydeck_chart(pdk.Deck(
        layers=[pdk.Layer(
            "ArcLayer", data=arc_sample,
            get_source_position=["pickup_lon", "pickup_lat"],
            get_target_position=["dropoff_lon", "dropoff_lat"],
            get_source_color=[30, 120, 255, 220],
            get_target_color=[255, 60, 60, 220],
            auto_highlight=True,
            width_min_pixels=2,
            width_max_pixels=6,
            pickable=True,
        )],
        initial_view_state=pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=12,
            pitch=40,
            bearing=0,
        ),
        map_style=CARTO_LIGHT,
    ), height=500)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Data Preview
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown(f"Showing **{min(50, len(df))}** of **{len(df):,}** trips after filters")
    st.dataframe(df.head(50), use_container_width=True, hide_index=True)
