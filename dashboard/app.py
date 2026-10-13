"""
Jan-Vani: Streamlit Officer & Municipal Head Dashboard
Implements the 5 views specified in Section 6 of the Build Plan:
1. Overview (KPI Cards, Language Breakdown, Resolution Metrics)
2. Ward Map (Folium Map with Ward Polygons, Heatmap, and Markers)
3. Ticket Table (Sortable, Filterable, CSV Export)
4. Trends (Plotly Daily/Weekly Timeseries, Category Distribution)
5. Ticket Detail (Transcript, Audio Player, GPS, Merged Duplicate Timeline)
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import json
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

from backend.database import SessionLocal, Ticket, Officer
from action.ward_routing import GEOJSON_PATH

# Streamlit Page Config
st.set_page_config(
    page_title="Jan-Vani Civic Dashboard | Nagpur",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Okabe-Ito Palette
PALETTE = {
    "orange": "#E69F00",
    "skyblue": "#56B4E9",
    "bluishgreen": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermilion": "#D55E00",
    "reddishpurple": "#CC79A7"
}

# Session state initialization
if "selected_ticket_id" not in st.session_state:
    st.session_state.selected_ticket_id = None
if "selected_ward" not in st.session_state:
    st.session_state.selected_ward = "ALL"

@st.cache_data(ttl=15)
def fetch_tickets():
    db = SessionLocal()
    try:
        tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).all()
        data = [t.to_dict() for t in tickets]
        return pd.DataFrame(data)
    finally:
        db.close()

df_tickets = fetch_tickets()

# Sidebar: Role & Global Filters
st.sidebar.title("🎙️ जन-वाणी (Jan-Vani)")
st.sidebar.caption("Nagpur Municipal Corporation Grievance Portal")

# Officer Role Selection
role = st.sidebar.selectbox(
    "👮 Officer Role / पद",
    ["Municipal Commissioner (सर्व प्रभाग)", "Ward 2 Officer (Dharampeth)", "Ward 4 Officer (Dhantoli)"],
    index=0
)

if "Ward 2" in role:
    st.session_state.selected_ward = "WARD-02"
elif "Ward 4" in role:
    st.session_state.selected_ward = "WARD-04"

# Honesty rule for data banner (Section 6.2)
st.sidebar.info("ℹ️ **Honesty Rule:** Data reflects live pipeline & seeded demonstration cases. Real benchmarks are in testing report.")

# Navigation View Selection
view = st.sidebar.radio(
    "📌 दृश्य निवडा / Select View",
    ["1. Overview (आढावा)", "2. Ward Map (प्रभाग नकाशा)", "3. Ticket Table (तक्रारी सूची)", "4. Trends (कल व आलेख)", "5. Ticket Detail (तपशील)"],
    index=0
)

# Filter Data according to active ward
if st.session_state.selected_ward != "ALL" and not df_tickets.empty:
    df_filtered = df_tickets[df_tickets["ward_id"] == st.session_state.selected_ward]
else:
    df_filtered = df_tickets

# Top Banner
st.title("जन-वाणी: प्रभाग तक्रार निवारण डॅशबोर्ड")
st.markdown("Vernacular Voice Assistant for Civic Grievance Redressal • NMC Nagpur")

# -------------------------------------------------------------
# VIEW 1: OVERVIEW
# -------------------------------------------------------------
if "1. Overview" in view:
    st.subheader("📊 मुख्य कार्यप्रदर्शन निर्देशांक (Key Performance Indicators)")

    total_tickets = len(df_filtered)
    open_tickets = len(df_filtered[df_filtered["status"] == "Open"]) if not df_filtered.empty else 0
    in_prog = len(df_filtered[df_filtered["status"] == "In Progress"]) if not df_filtered.empty else 0
    resolved = len(df_filtered[df_filtered["status"] == "Resolved"]) if not df_filtered.empty else 0
    merged_count = int(df_filtered["duplicate_count"].sum() - len(df_filtered)) if not df_filtered.empty else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("एकूण तिकीट (Total)", total_tickets)
    col2.metric("प्रलंबित (Open)", open_tickets, delta="-urgent", delta_color="inverse")
    col3.metric("कार्यरत (In Progress)", in_prog)
    col4.metric("निवारण (Resolved)", resolved, delta="+closed")
    col5.metric("एकत्रित डुप्लिकेट्स (Merged)", merged_count, help="Complaints merged within 50m and 48h")

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🗣️ तक्रारींची भाषा (Languages Used)")
        if not df_filtered.empty:
            lang_counts = df_filtered["language"].value_counts().reset_index()
            lang_counts.columns = ["Language", "Count"]
            lang_counts["Language"] = lang_counts["Language"].map({"mr": "मराठी (Marathi)", "hi": "हिंदी (Hindi)", "en": "English"})
            fig_lang = px.pie(
                lang_counts, values="Count", names="Language",
                color_discrete_sequence=[PALETTE["orange"], PALETTE["skyblue"], PALETTE["bluishgreen"]]
            )
            st.plotly_chart(fig_lang, use_container_width=True)

    with c2:
        st.markdown("#### 📑 तक्रार वर्गवारी (Category Distribution)")
        if not df_filtered.empty:
            cat_counts = df_filtered["category"].value_counts().reset_index()
            cat_counts.columns = ["Category", "Count"]
            fig_cat = px.bar(
                cat_counts, x="Category", y="Count",
                color="Category",
                color_discrete_sequence=[PALETTE["bluishgreen"], PALETTE["orange"], PALETTE["blue"], PALETTE["vermilion"]]
            )
            st.plotly_chart(fig_cat, use_container_width=True)

# -------------------------------------------------------------
# VIEW 2: WARD MAP
# -------------------------------------------------------------
elif "2. Ward Map" in view:
    st.subheader("🗺️ नागपूर प्रभाग नकाशा व हीटमॅप (Nagpur Ward Heatmap & Tickets)")
    st.caption("क्लिक करा आणि प्रभागातील तक्रारींची घनता आणि एकत्रित समस्या तपासा")

    m = folium.Map(location=[21.1458, 79.0882], zoom_start=12, tiles="OpenStreetMap")

    # Add GeoJSON Wards if present
    if GEOJSON_PATH.exists():
        with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
            geo_data = json.load(f)
            folium.GeoJson(
                geo_data,
                name="Nagpur Wards",
                style_function=lambda x: {
                    "fillColor": PALETTE["skyblue"],
                    "color": PALETTE["blue"],
                    "weight": 2,
                    "fillOpacity": 0.15
                },
                tooltip=folium.GeoJsonTooltip(fields=["ward_name", "ward_id", "zone"], aliases=["Ward:", "ID:", "Zone:"])
            ).addTo(m)

    # Add markers
    if not df_filtered.empty:
        heat_points = []
        for _, row in df_filtered.iterrows():
            lat, lon = row["latitude"], row["longitude"]
            heat_points.append([lat, lon, row["duplicate_count"]])

            color = PALETTE["vermilion"] if row["urgency"] == "High" else (PALETTE["orange"] if row["urgency"] == "Medium" else PALETTE["bluishgreen"])
            popup_html = f"""
            <b>{row['id']}</b> ({row['status']})<br>
            <b>Ward:</b> {row['ward_name']}<br>
            <b>Category:</b> {row['category']}<br>
            <b>Urgency:</b> {row['urgency']}<br>
            <b>Merged Citizens:</b> {row['duplicate_count']}<br>
            <i>"{row['transcript'][:60]}..."</i>
            """
            folium.CircleMarker(
                location=[lat, lon],
                radius=8 + (row["duplicate_count"] * 2),
                color="#ffffff",
                weight=2,
                fill_color=color,
                fill_opacity=0.85,
                popup=folium.Popup(popup_html, max_width=250)
            ).addTo(m)

        HeatMap(heat_points, radius=18, blur=15).addTo(m)

    st_folium(m, width=1100, height=500)

# -------------------------------------------------------------
# VIEW 3: TICKET TABLE
# -------------------------------------------------------------
elif "3. Ticket Table" in view:
    st.subheader("📋 सर्व तक्रारींची यादी (Ticket Console)")

    col_f1, col_f2, col_f3 = st.columns(3)
    cat_filter = col_f1.selectbox("Filter Category", ["ALL"] + list(df_tickets["category"].unique()))
    status_filter = col_f2.selectbox("Filter Status", ["ALL", "Open", "In Progress", "Resolved"])
    urgency_filter = col_f3.selectbox("Filter Urgency", ["ALL", "Low", "Medium", "High"])

    tbl = df_filtered.copy()
    if cat_filter != "ALL":
        tbl = tbl[tbl["category"] == cat_filter]
    if status_filter != "ALL":
        tbl = tbl[tbl["status"] == status_filter]
    if urgency_filter != "ALL":
        tbl = tbl[tbl["urgency"] == urgency_filter]

    display_cols = ["id", "ward_name", "category", "sub_category", "urgency", "status", "duplicate_count", "created_at"]
    st.dataframe(tbl[display_cols], use_container_width=True)

    csv = tbl.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Export CSV", data=csv, file_name="jan_vani_tickets.csv", mime="text/csv")

    st.markdown("#### तपशील पाहण्यासाठी तिकीट निवडा (Select Ticket for Detail View):")
    chosen = st.selectbox("Ticket ID", tbl["id"].tolist())
    if st.button("तपशील उघडा (Open Ticket Detail)"):
        st.session_state.selected_ticket_id = chosen
        st.rerun()

# -------------------------------------------------------------
# VIEW 4: TRENDS
# -------------------------------------------------------------
elif "4. Trends" in view:
    st.subheader("📈 कल व विश्लेषण (Grievance Trends & Velocity)")

    if not df_filtered.empty:
        df_copy = df_filtered.copy()
        df_copy["created_at"] = pd.to_datetime(df_copy["created_at"])
        df_copy["date"] = df_copy["created_at"].dt.date

        daily_counts = df_copy.groupby(["date", "category"]).size().reset_index(name="count")
        fig_trend = px.line(
            daily_counts, x="date", y="count", color="category",
            title="दैनिक तक्रारींची संख्या (Daily Grievances by Category)",
            markers=True
        )
        st.plotly_chart(fig_trend, use_container_width=True)

        fig_urg = px.bar(
            df_filtered, x="ward_name", color="urgency",
            title="प्रभागानिहाय तीव्रता (Urgency Severity by Ward)",
            barmode="group",
            color_discrete_map={"High": PALETTE["vermilion"], "Medium": PALETTE["orange"], "Low": PALETTE["bluishgreen"]}
        )
        st.plotly_chart(fig_urg, use_container_width=True)

# -------------------------------------------------------------
# VIEW 5: TICKET DETAIL
# -------------------------------------------------------------
elif "5. Ticket Detail" in view:
    ticket_id = st.session_state.selected_ticket_id or (df_filtered["id"].iloc[0] if not df_filtered.empty else None)
    st.subheader(f"🔍 तिकीट तपशील: {ticket_id}")

    if ticket_id and not df_filtered.empty and ticket_id in df_tickets["id"].values:
        row = df_tickets[df_tickets["id"] == ticket_id].iloc[0]

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**प्रभाग (Ward):** {row['ward_name']} ({row['ward_id']})")
            st.markdown(f"**श्रेणी (Category):** {row['category']} - {row['sub_category']}")
            st.markdown(f"**तीव्रता (Urgency):** {row['urgency']}")
            st.markdown(f"**स्थिती (Status):** `{row['status']}`")
            st.markdown(f"**एकत्रित नागरिक (Duplicates Merged):** {row['duplicate_count']}")
        with col_b:
            st.markdown(f"**स्थान (GPS Coordinates):** `{row['latitude']}, {row['longitude']}`")
            st.markdown(f"**कालावधी (Duration Reported):** {row['duration_text'] or 'Not specified'}")
            st.markdown(f"**एआय आत्मविश्वास (Confidence):** `{round(row['confidence'] * 100, 1)}%`")

        st.info(f"🗣️ **नागरिकाचा मूळ ऑडिओ उतारा (Transcript):**\n\"{row['transcript']}\"")
        st.success(f"🌐 **इंग्रजी सारांश (Summary EN):**\n{row['summary_en']}")

        # Status Update Action
        st.markdown("#### ⚡ स्थिती अद्ययावत करा (Update Status)")
        new_status = st.selectbox("New Status", ["Open", "In Progress", "Resolved"], index=["Open", "In Progress", "Resolved"].index(row['status']))
        note = st.text_input("Officer Action Note", placeholder="उदा. पथक रवाना झाले आहे...")
        if st.button("स्थिती सेव्ह करा (Save Status)"):
            db = SessionLocal()
            try:
                t_obj = db.query(Ticket).filter(Ticket.id == ticket_id).first()
                if t_obj:
                    t_obj.status = new_status
                    history = json.loads(t_obj.status_history or "[]")
                    history.append({"time": str(pd.Timestamp.now()), "status": new_status, "note": note})
                    t_obj.status_history = json.dumps(history)
                    db.commit()
                    st.success(f"Ticket {ticket_id} updated to {new_status}!")
                    fetch_tickets.clear()
                    st.rerun()
            finally:
                db.close()
    else:
        st.warning("कोणतेही तिकीट निवडलेले नाही. कृपया 'Ticket Table' मध्ये जाऊन तिकीट निवडा.")
