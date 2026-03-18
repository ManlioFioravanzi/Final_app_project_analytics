import streamlit as st
import pandas as pd

st.set_page_config(page_title="Car Sharing Dashboard", layout="wide")

st.title("🚗 Car Sharing Dashboard")

# ─────────────────────────────────────────────
# 1. Load Data
# ─────────────────────────────────────────────

DATA_DIR = "Session-04-car_sharing_data_for_Streamlit"

@st.cache_data
def load_data():
    trips  = pd.read_csv(f"{DATA_DIR}/trips.csv")
    cars   = pd.read_csv(f"{DATA_DIR}/cars.csv")
    cities = pd.read_csv(f"{DATA_DIR}/cities.csv")
    return trips, cars, cities

trips, cars, cities = load_data()

# ─────────────────────────────────────────────
# 2. Join all dataframes
# ─────────────────────────────────────────────

# Merge trips with cars (joining on car_id)
trips_merged = trips.merge(
    cars,
    left_on="car_id",
    right_on="id",
    suffixes=("", "_car")
)

# Merge with cities for car's city (joining on city_id)
trips_merged = trips_merged.merge(
    cities,
    on="city_id"
)

# ─────────────────────────────────────────────
# 3. Clean useless columns
# ─────────────────────────────────────────────

trips_merged = trips_merged.drop(
    columns=["id_car", "city_id", "customer_id", "id", "car_id"],
    errors="ignore"
)

# ─────────────────────────────────────────────
# 4. Update date format
# ─────────────────────────────────────────────

trips_merged["pickup_time"]   = pd.to_datetime(trips_merged["pickup_time"])
trips_merged["dropoff_time"]  = pd.to_datetime(trips_merged["dropoff_time"])
trips_merged["pickup_date"]   = trips_merged["pickup_time"].dt.date

# Compute trip duration in hours
trips_merged["trip_duration_h"] = (
    (trips_merged["dropoff_time"] - trips_merged["pickup_time"])
    .dt.total_seconds() / 3600
)

# ─────────────────────────────────────────────
# 5. Sidebar Filters
# ─────────────────────────────────────────────

st.sidebar.header("Filters")

all_brands = sorted(trips_merged["brand"].unique())
cars_brand = st.sidebar.multiselect(
    "Select the Car Brand",
    options=all_brands,
    default=all_brands
)

if cars_brand:
    trips_merged = trips_merged[trips_merged["brand"].isin(cars_brand)]

# ─────────────────────────────────────────────
# 6. Business Metrics
# ─────────────────────────────────────────────

st.subheader("Business Performance Metrics")

total_trips    = len(trips_merged)
total_distance = trips_merged["distance"].sum()
top_car        = trips_merged.groupby("model")["revenue"].sum().idxmax()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total Trips", value=total_trips)
with col2:
    st.metric(label="Top Car Model by Revenue", value=top_car)
with col3:
    st.metric(label="Total Distance (km)", value=f"{total_distance:,.2f}")

# ─────────────────────────────────────────────
# 7. Preview dataframe
# ─────────────────────────────────────────────

st.subheader("Data Preview")
st.write(trips_merged.head())

# ─────────────────────────────────────────────
# 8. Visualizations
# ─────────────────────────────────────────────

st.subheader("Visualizations")

# --- Chart 1: Trips Over Time ---
st.markdown("#### Trips Over Time")
trips_over_time = (
    trips_merged.groupby("pickup_date")
    .size()
    .reset_index(name="trip_count")
    .set_index("pickup_date")
)
st.line_chart(trips_over_time)

# --- Chart 2: Revenue Per Car Model ---
st.markdown("#### Revenue Per Car Model")
revenue_per_model = (
    trips_merged.groupby("model")["revenue"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
    .set_index("model")
)
st.bar_chart(revenue_per_model)

# --- Chart 3: Cumulative Revenue Growth Over Time ---
st.markdown("#### Cumulative Revenue Growth Over Time")
cumulative_revenue = (
    trips_merged.groupby("pickup_date")["revenue"]
    .sum()
    .cumsum()
    .reset_index()
    .set_index("pickup_date")
)
st.area_chart(cumulative_revenue)

# --- Chart 4: Revenue by City ---
st.markdown("#### Revenue by City")
revenue_by_city = (
    trips_merged.groupby("city_name")["revenue"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
    .set_index("city_name")
)
st.bar_chart(revenue_by_city)

# --- Chart 5 (Bonus): Average Trip Duration by City ---
st.markdown("#### Average Trip Duration by City (hours)")
avg_duration_city = (
    trips_merged.groupby("city_name")["trip_duration_h"]
    .mean()
    .sort_values(ascending=False)
    .reset_index()
    .set_index("city_name")
)
st.bar_chart(avg_duration_city)

# --- Chart 6 (Bonus): Number of Trips Per Car Model ---
st.markdown("#### Number of Trips Per Car Model")
trips_per_model = (
    trips_merged.groupby("model")
    .size()
    .sort_values(ascending=False)
    .reset_index(name="trip_count")
    .set_index("model")
)
st.bar_chart(trips_per_model)
