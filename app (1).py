import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


# ---------------------------------------------------------
# STREAMLIT CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Maharashtra Economic Diversity Index",
    page_icon="🗺️",
    layout="wide",
)

st.title("Maharashtra Economic Diversity Index")
st.caption("District-wise Economic Diversity Index, Rank and Activity Profile")


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------
DEFAULT_EXCEL = "economic_diversity_ranking (1).xlsx"
GEOJSON_URL = (
    "https://cdn.jsdelivr.net/gh/udit-001/india-maps-data@2884453/"
    "geojson/states/maharashtra.geojson"
)

# Names used in different Maharashtra datasets are normalized here.
NAME_MAP = {
    "AHMEDNAGAR": "AHILYANAGAR",
    "AHMED NAGAR": "AHILYANAGAR",
    "AHILYANAGAR": "AHILYANAGAR",
    "AURANGABAD": "CHHATRAPATI SAMBHAJINAGAR",
    "CHHATRAPATI SAMBHAJI NAGAR": "CHHATRAPATI SAMBHAJINAGAR",
    "CHHATRAPATI SAMBHAJINAGAR": "CHHATRAPATI SAMBHAJINAGAR",
    "OSMANABAD": "DHARASHIV",
    "DHARASHIV": "DHARASHIV",
    "GONDIA": "GONDIYA",
    "MUMBAI CITY": "MUMBAI",
    "MUMBAI SUBURBAN": "MUMBAI",
}

REQUIRED_COLUMNS = ["District", "Normalized_Diversity", "Rank"]


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def normalize_name(value):
    if pd.isna(value):
        return ""
    value = str(value).strip().upper()
    value = " ".join(value.split())
    return NAME_MAP.get(value, value)


def display_name(value):
    name = str(value).strip().upper()
    pretty = {
        "AHILYANAGAR": "Ahilyanagar",
        "CHHATRAPATI SAMBHAJINAGAR": "Chhatrapati Sambhajinagar",
        "DHARASHIV": "Dharashiv",
        "GONDIYA": "Gondiya",
    }
    return pretty.get(name, name.title())


@st.cache_data(show_spinner=False)
def load_excel(source):
    df = pd.read_excel(source, sheet_name=0)
    df.columns = [str(c).strip() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "Excel मध्ये आवश्यक columns सापडले नाहीत: " + ", ".join(missing)
        )

    df["District"] = df["District"].map(normalize_name)
    df["Normalized_Diversity"] = pd.to_numeric(
        df["Normalized_Diversity"], errors="coerce"
    )
    df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce")

    # Activity count is useful for the dashboard but does not replace the
    # source Normalized_Diversity metric.
    if "Total_Activity" in df.columns:
        df["Total_Activity"] = pd.to_numeric(df["Total_Activity"], errors="coerce")

    # Classify the normalized diversity index into three easy-to-read levels.
    df["Diversity Level"] = pd.cut(
        df["Normalized_Diversity"],
        bins=[-float("inf"), 0.60, 0.70, float("inf")],
        labels=["Low", "Medium", "High"],
        include_lowest=True,
    )

    df["District Display"] = df["District"].map(display_name)
    return df.sort_values("Rank", na_position="last").reset_index(drop=True)


@st.cache_data(ttl=86400, show_spinner=False)
def load_geojson():
    response = requests.get(GEOJSON_URL, timeout=20)
    response.raise_for_status()
    geojson = response.json()
    return geojson


def find_geojson_name_property(geojson):
    """Find the district-name property used by the downloaded GeoJSON."""
    candidates = [
        "district",
        "District",
        "district_name",
        "DISTRICT",
        "dtname",
        "DTNAME",
        "name",
        "NAME",
    ]
    for candidate in candidates:
        for feature in geojson.get("features", []):
            if candidate in feature.get("properties", {}):
                return candidate
    return None


def prepare_geojson(geojson, name_property):
    """Add a normalized district key so Excel and GeoJSON names can match."""
    for feature in geojson.get("features", []):
        props = feature.setdefault("properties", {})
        raw = props.get(name_property)
        props["district_map_key"] = normalize_name(raw)
    return geojson


def get_all_points(coords):
    points = []

    def extract(obj):
        if isinstance(obj, (list, tuple)):
            if (
                len(obj) >= 2
                and isinstance(obj[0], (int, float))
                and isinstance(obj[1], (int, float))
            ):
                points.append((obj[0], obj[1]))
            else:
                for item in obj:
                    extract(item)

    extract(coords)
    return points


def make_label_data(geojson, name_property, df):
    label_data = []
    rank_lookup = df.set_index("District")["Rank"].to_dict()

    for feature in geojson.get("features", []):
        props = feature.get("properties", {})
        district = normalize_name(props.get(name_property))
        geometry = feature.get("geometry") or {}
        coords = geometry.get("coordinates")

        if not coords:
            continue

        points = get_all_points(coords)
        if not points:
            continue

        avg_lon = sum(p[0] for p in points) / len(points)
        avg_lat = sum(p[1] for p in points) / len(points)

        label_data.append(
            {
                "District": district,
                "lon": avg_lon,
                "lat": avg_lat,
                "Rank": rank_lookup.get(district),
            }
        )

    return pd.DataFrame(label_data)


# ---------------------------------------------------------
# SIDEBAR - DATA INPUT
# ---------------------------------------------------------
st.sidebar.header("Data")

uploaded_excel = st.sidebar.file_uploader(
    "Excel file upload करा",
    type=["xlsx", "xls"],
    help="Default म्हणून app च्या folder मधील economic_diversity_ranking (1).xlsx वापरला जाईल.",
)

uploaded_geojson = st.sidebar.file_uploader(
    "GeoJSON upload करा (optional)",
    type=["geojson", "json"],
    help="Online Maharashtra district GeoJSON उपलब्ध नसेल तर local GeoJSON upload करा.",
)


# ---------------------------------------------------------
# LOAD DATA
# -------------------------------------------------P--------
try:
    if uploaded_excel is not None:
        df = load_excel(uploaded_excel)
    elif Path(DEFAULT_EXCEL).exists():
        df = load_excel(DEFAULT_EXCEL)
    else:
        st.error(
            f"'{DEFAULT_EXCEL}' file सापडली नाही. कृपया sidebar मधून Excel upload करा."
        )
        st.stop()
except Exception as exc:
    st.error(f"Excel वाचताना error आला: {exc}")
    st.stop()


# ---------------------------------------------------------
# TOP KPIs
# ---------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Districts", len(df))
with col2:
    st.metric("Highest Diversity", f"{df['Normalized_Diversity'].max():.4f}")
with col3:
    top_district = df.loc[df["Normalized_Diversity"].idxmax(), "District Display"]
    st.metric("Rank #1 District", top_district)
with col4:
    st.metric("Average Diversity", f"{df['Normalized_Diversity'].mean():.4f}")


# ---------------------------------------------------------
# FILTERS
# ---------------------------------------------------------
st.sidebar.header("Filters")
levels = st.sidebar.multiselect(
    "Diversity Level",
    options=["High", "Medium", "Low"],
    default=["High", "Medium", "Low"],
)

rank_range = st.sidebar.slider(
    "Rank range",
    min_value=int(df["Rank"].min()),
    max_value=int(df["Rank"].max()),
    value=(int(df["Rank"].min()), int(df["Rank"].max())),
)

filtered = df[
    df["Diversity Level"].astype(str).isin(levels)
    & df["Rank"].between(rank_range[0], rank_range[1])
].copy()


# ---------------------------------------------------------
# MAP
# ---------------------------------------------------------
st.subheader("District-wise Economic Diversity Map")

try:
    if uploaded_geojson is not None:
        geojson = json.load(uploaded_geojson)
    else:
        geojson = load_geojson()

    geo_name_property = find_geojson_name_property(geojson)
    if not geo_name_property:
        raise ValueError("GeoJSON मध्ये district-name property सापडली नाही.")

    geojson = prepare_geojson(geojson, geo_name_property)

    # Plotly map data uses a stable normalized key for matching.
    map_df = filtered.copy()
    map_df["district_map_key"] = map_df["District"]

    fig = px.choropleth(
        map_df,
        geojson=geojson,
        locations="district_map_key",
        featureidkey="properties.district_map_key",
        color="Diversity Level",
        hover_name="District Display",
        hover_data={
            "Normalized_Diversity": ":.4f",
            "Rank": True,
            "Diversity Level": True,
            "district_map_key": False,
        },
        color_discrete_map={
            "Low": "#B22222",
            "Medium": "#B8860B",
            "High": "#006400",
        },
    )

    labels = make_label_data(geojson, geo_name_property, filtered)
    if not labels.empty:
        labels["District Label"] = labels["District"].map(display_name)
        label_text = []
        for name, rank in zip(labels["District Label"], labels["Rank"]):
            if pd.notna(rank):
                label_text.append(f"<b>{name}</b><br>Rank: {int(rank)}")
            else:
                label_text.append(f"<b>{name}</b><br>Rank: No Data")

        fig.add_trace(
            go.Scattergeo(
                lon=labels["lon"],
                lat=labels["lat"],
                text=label_text,
                mode="text",
                textfont=dict(size=9, color="black"),
                hoverinfo="text",
                showlegend=False,
            )
        )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        projection_type="mercator",
    )

    fig.update_layout(
        height=650,
        margin=dict(r=0, t=10, l=0, b=0),
        legend_title_text="Diversity Level",
    )

    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

except Exception as exc:
    st.warning(
        "Map तयार करताना GeoJSON संबंधित समस्या आली. "
        "कृपया sidebar मधून Maharashtra district GeoJSON upload करा."
    )
    st.code(str(exc))


# ---------------------------------------------------------
# RANKING TABLE
# ---------------------------------------------------------
st.subheader("District Economic Diversity Ranking")

show_cols = [
    "District Display",
    "Normalized_Diversity",
    "Rank",
    "Diversity Level",
]
if "Total_Activity" in filtered.columns:
    show_cols.append("Total_Activity")

result_table = filtered[show_cols].sort_values("Rank").rename(
    columns={
        "District Display": "District",
        "Normalized_Diversity": "Normalized Diversity",
        "Diversity Level": "Diversity Level",
        "Total_Activity": "Total Activity",
    }
)

st.dataframe(
    result_table,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Normalized Diversity": st.column_config.NumberColumn(format="%.4f"),
        "Rank": st.column_config.NumberColumn(format="%d"),
    },
)


# ---------------------------------------------------------
# BAR CHART
# ---------------------------------------------------------
st.subheader("Top Districts by Normalized Diversity")

bar_df = df.sort_values("Normalized_Diversity", ascending=False).head(15).sort_values(
    "Normalized_Diversity"
)

bar_fig = px.bar(
    bar_df,
    x="Normalized_Diversity",
    y="District Display",
    orientation="h",
    text="Rank",
    labels={
        "Normalized_Diversity": "Normalized Diversity",
        "District Display": "District",
        "Rank": "Rank",
    },
)
bar_fig.update_traces(texttemplate="Rank %{text}", textposition="outside")
bar_fig.update_layout(height=550, margin=dict(l=0, r=20, t=10, b=10))
st.plotly_chart(bar_fig, use_container_width=True, config={"displaylogo": False})


# ---------------------------------------------------------
# DOWNLOAD FILTERED DATA
# ---------------------------------------------------------
csv_data = result_table.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Filtered ranking CSV download करा",
    data=csv_data,
    file_name="economic_diversity_ranking_filtered.csv",
    mime="text/csv",
)
