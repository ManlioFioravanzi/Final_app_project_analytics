import streamlit as st
import pandas as pd
import pydeck as pdk
import os

st.set_page_config(
    page_title="Car Sharing Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Full app dark background ── */
    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stApp"], .main, .block-container {
        background-color: #0f1117 !important;
        color: #e8ecf4 !important;
    }

    /* ── Sidebar — same dark color as app ── */
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div:first-child {
        background-color: #0f1117 !important;
        border-right: 1px solid #2d3250;
    }

    /* Hamburger button (☰) color */
    [data-testid="collapsedControl"] {
        color: #e8ecf4 !important;
    }
    [data-testid="collapsedControl"] svg {
        fill: #e8ecf4 !important;
    }

    /* ── Metric cards ── */
    div[data-testid="metric-container"] {
        background-color: #1e2130;
        border: 1px solid #2d3250;
        border-radius: 12px;
        padding: 16px 20px;
    }
    div[data-testid="metric-container"] label {
        color: #8b9fca !important;
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #e8ecf4 !important;
        font-size: 1.8rem;
        font-weight: 700;
    }

    /* ── Section headers inside sidebar ── */
    .section-header {
        color: #7c8db5;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.4rem;
        padding-top: 0.5rem;
    }

    /* ── Tabs ── */
    button[data-baseweb="tab"] {
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: #8b9fca !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #e8ecf4 !important;
    }

    /* ── Dataframe ── */
    [data-testid="stDataFrame"] { background-color: #1e2130; border-radius: 10px; }

    /* ── Dividers ── */
    hr { border-color: #2d3250 !important; }

    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Data Loading ──────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "Session-04-car_sharing_data_for_Streamlit")

@st.cache_data
def load_data():
    trips  = pd.read_csv(f"{DATA_DIR}/trips.csv")
    cars   = pd.read_csv(f"{DATA_DIR}/cars.csv")
    cities = pd.read_csv(f"{DATA_DIR}/cities.csv")
    return trips, cars, cities

trips, cars, cities = load_data()

# ── Merge & Transform ─────────────────────────────────────────────────────────
trips_merged = trips.merge(cars, left_on="car_id", right_on="id", suffixes=("", "_car"))
trips_merged = trips_merged.merge(cities, on="city_id")
trips_merged = trips_merged.drop(
    columns=["id_car", "city_id", "customer_id", "id", "car_id"], errors="ignore"
)

trips_merged["pickup_time"]      = pd.to_datetime(trips_merged["pickup_time"])
trips_merged["dropoff_time"]     = pd.to_datetime(trips_merged["dropoff_time"])
trips_merged["pickup_date"]      = trips_merged["pickup_time"].dt.date
trips_merged["trip_duration_h"]  = (
    (trips_merged["dropoff_time"] - trips_merged["pickup_time"]).dt.total_seconds() / 3600
)

# ── Sidebar Filters ───────────────────────────────────────────────────────────
st.sidebar.image("https://img.icons8.com/fluency/96/car.png", width=56)
st.sidebar.title("Car Sharing")
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
st.markdown("Real-time analytics across cities, brands and time periods.")
st.markdown("---")

# ── KPI Metrics ───────────────────────────────────────────────────────────────
total_trips    = len(df)
total_revenue  = df["revenue"].sum()
total_distance = df["distance"].sum()
top_car        = df.groupby("model")["revenue"].sum().idxmax() if not df.empty else "—"
avg_duration   = df["trip_duration_h"].mean()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🗺️ Total Trips",          f"{total_trips:,}")
c2.metric("💰 Total Revenue",        f"€{total_revenue:,.0f}")
c3.metric("📍 Total Distance (km)",  f"{total_distance:,.0f}")
c4.metric("🏆 Top Model by Revenue", top_car)
c5.metric("⏱️ Avg Trip Duration",    f"{avg_duration:.1f} h")

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊  Charts", "🗺️  Geographic Maps", "🔍  Data Preview"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Charts
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Trips Over Time")
        trips_over_time = (
            df.groupby("pickup_date").size()
            .reset_index(name="Trips").set_index("pickup_date")
        )
        st.line_chart(trips_over_time, height=260)

        st.markdown("#### Revenue Per Car Model")
        revenue_per_model = (
            df.groupby("model")["revenue"].sum()
            .sort_values(ascending=False)
            .reset_index().rename(columns={"revenue": "Revenue"}).set_index("model")
        )
        st.bar_chart(revenue_per_model, height=280)

        st.markdown("#### Number of Trips Per Car Model")
        trips_per_model = (
            df.groupby("model").size()
            .sort_values(ascending=False)
            .reset_index(name="Trips").set_index("model")
        )
        st.bar_chart(trips_per_model, height=280)

    with col_right:
        st.markdown("#### Cumulative Revenue Growth")
        cumulative_revenue = (
            df.groupby("pickup_date")["revenue"].sum()
            .cumsum().reset_index().rename(columns={"revenue": "Cumulative Revenue"})
            .set_index("pickup_date")
        )
        st.area_chart(cumulative_revenue, height=260)

        st.markdown("#### Revenue by City")
        revenue_by_city = (
            df.groupby("city_name")["revenue"].sum()
            .sort_values(ascending=False)
            .reset_index().rename(columns={"revenue": "Revenue", "city_name": "City"})
            .set_index("City")
        )
        st.bar_chart(revenue_by_city, height=280)

        st.markdown("#### Avg Trip Duration by City (hours)")
        avg_dur_city = (
            df.groupby("city_name")["trip_duration_h"].mean()
            .sort_values(ascending=False)
            .reset_index().rename(columns={"trip_duration_h": "Avg Duration (h)", "city_name": "City"})
            .set_index("City")
        )
        st.bar_chart(avg_dur_city, height=280)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Geographic Maps
# ══════════════════════════════════════════════════════════════════════════════
with tab2:

    # ── Heatmap of Trip Pickup Locations ──────────────────────────────────────
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
        radiusPixels=40,
        intensity=1,
        threshold=0.03,
        opacity=0.85,
        color_range=[
            [0,   0,   255, 0],
            [0,   128, 255, 80],
            [0,   255, 128, 120],
            [255, 255, 0,   160],
            [255, 128, 0,   200],
            [255, 0,   0,   240],
        ],
    )

    view_state = pdk.ViewState(
        latitude=heatmap_data["lat"].mean(),
        longitude=heatmap_data["lon"].mean(),
        zoom=4,
        pitch=0,
    )

    st.pydeck_chart(pdk.Deck(
        layers=[heatmap_layer],
        initial_view_state=view_state,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    ))

    st.markdown("---")

    # ── City Bubble Map ───────────────────────────────────────────────────────
    st.markdown("#### 🌍 Revenue & Trips by City")
    st.caption("Bubble size = total revenue · Color = number of trips")

    city_stats = (
        df.groupby("city_name")
        .agg(total_revenue=("revenue", "sum"), trip_count=("revenue", "count"))
        .reset_index()
    )
    city_coords = cities[["city_name", "city_lat", "city_long"]].copy()
    city_map_df = city_stats.merge(city_coords, on="city_name")
    city_map_df["radius"] = (city_map_df["total_revenue"] / city_map_df["total_revenue"].max() * 80000).clip(lower=5000)

    max_trips = city_map_df["trip_count"].max()
    city_map_df["color_r"] = (255 * city_map_df["trip_count"] / max_trips).astype(int)
    city_map_df["color_g"] = (100 * (1 - city_map_df["trip_count"] / max_trips)).astype(int)
    city_map_df["color_b"] = 200

    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=city_map_df,
        get_position=["city_long", "city_lat"],
        get_radius="radius",
        get_fill_color=["color_r", "color_g", "color_b", 180],
        get_line_color=[255, 255, 255, 100],
        stroked=True,
        line_width_min_pixels=1,
        pickable=True,
    )

    text_layer = pdk.Layer(
        "TextLayer",
        data=city_map_df,
        get_position=["city_long", "city_lat"],
        get_text="city_name",
        get_size=14,
        get_color=[255, 255, 255, 220],
        get_alignment_baseline="'bottom'",
        get_anchor="'middle'",
    )

    city_view = pdk.ViewState(
        latitude=city_map_df["city_lat"].mean(),
        longitude=city_map_df["city_long"].mean(),
        zoom=3.5,
        pitch=30,
    )

    st.pydeck_chart(pdk.Deck(
        layers=[scatter_layer, text_layer],
        initial_view_state=city_view,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        tooltip={
            "html": "<b>{city_name}</b><br/>Revenue: €{total_revenue}<br/>Trips: {trip_count}",
            "style": {"backgroundColor": "#1e2130", "color": "#e8ecf4", "border": "1px solid #2d3250"},
        },
    ))

    st.markdown("---")

    # ── Arc Layer: Pickup → Dropoff ───────────────────────────────────────────
    st.markdown("#### ✈️ Trip Routes (Arc Map)")
    st.caption("Sample of 500 trips — arcs connect pickup to dropoff location")

    arc_sample = df[["pickup_lat", "pickup_lon", "dropoff_lat", "dropoff_lon", "revenue"]].dropna().sample(
        n=min(500, len(df)), random_state=42
    )

    arc_layer = pdk.Layer(
        "ArcLayer",
        data=arc_sample,
        get_source_position=["pickup_lon", "pickup_lat"],
        get_target_position=["dropoff_lon", "dropoff_lat"],
        get_source_color=[0, 128, 255, 140],
        get_target_color=[255, 80, 50, 140],
        auto_highlight=True,
        width_scale=0.0001,
        get_width="revenue",
        width_min_pixels=1,
        width_max_pixels=4,
        pickable=True,
    )

    arc_view = pdk.ViewState(
        latitude=arc_sample["pickup_lat"].mean(),
        longitude=arc_sample["pickup_lon"].mean(),
        zoom=4,
        pitch=45,
    )

    st.pydeck_chart(pdk.Deck(
        layers=[arc_layer],
        initial_view_state=arc_view,
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
    ))

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Data Preview
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown(f"Showing **{min(50, len(df))}** of **{len(df):,}** trips after filters")
    st.dataframe(
        df.head(50),
        use_container_width=True,
        hide_index=True,
    )
