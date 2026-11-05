import os
import streamlit as st
from db import init_db, add_player, get_player, count_players, get_all_players
from pdf_book import build_pdf

init_db()
st.set_page_config(page_title="Nextup", page_icon="🏏", layout="wide")
ROLES = ["Batsman", "Bowler", "All-rounder", "Wicketkeeper", "Raider", "Defender"]

if "drawn" not in st.session_state:
    st.session_state.drawn = []      # numbers already shown
if "current" not in st.session_state:
    st.session_state.current = None  # player currently on screen

mode = st.sidebar.radio("Mode", ["Register", "Auction", "Organizer"])

# ---------------- REGISTER ----------------
if mode == "Register":
    st.title("🏏 Player Registration")
    with st.form("register", clear_on_submit=True):
        name = st.text_input("Full name")
        role = st.selectbox("Role", ROLES)
        age = st.number_input("Age", min_value=10, max_value=70, value=20)
        village = st.text_input("Village")
        photo = st.file_uploader("Your photo", type=["jpg", "jpeg", "png"])
        submitted = st.form_submit_button("Register", type="primary")

    if submitted:
        if not name.strip() or not village.strip() or photo is None:
            st.error("Please fill every field and upload a photo.")
        else:
            pid = add_player(name.strip(), role, int(age), village.strip(), photo.getvalue())
            st.success(f"Registered! Your player number is {pid}.")


# ---------------- AUCTION ----------------
elif mode == "Auction":
    total = count_players()
    st.sidebar.markdown(f"**Registered players:** {total}")

    with st.sidebar.form("draw"):
        number = st.number_input("Number from the chit", min_value=1, step=1, value=1)
        show = st.form_submit_button("Show player", type="primary")

    if show:
        player = get_player(int(number))
        if player is None:
            st.sidebar.error(f"No player with number {int(number)}.")
        else:
            if player["id"] in st.session_state.drawn:
                st.sidebar.warning("This number was already shown.")
            else:
                st.session_state.drawn.append(player["id"])
            st.session_state.current = player

    st.sidebar.markdown("**Shown so far:** " + (", ".join(map(str, st.session_state.drawn)) or "none"))

    p = st.session_state.current
    if p is None:
        st.markdown("<h1 style='text-align:center;margin-top:30vh'>Nextup 🏏</h1>",
                    unsafe_allow_html=True)
    else:
        st.markdown(
            f"<h1 style='text-align:center;font-size:90px;margin:0'>Player #{p['id']}</h1>",
            unsafe_allow_html=True,
        )
        left, right = st.columns([1, 1])
        with left:
            st.image(p["photo_path"], use_container_width=True)
        with right:
            st.markdown(
                f"""
                <div style='font-size:64px;font-weight:700;margin-top:20px'>{p['name']}</div>
                <div style='font-size:44px;margin-top:30px'>Role: {p['role']}</div>
                <div style='font-size:44px'>Age: {p['age']}</div>
                <div style='font-size:44px'>Village: {p['village']}</div>
                """,
                unsafe_allow_html=True,
            )

# ---------------- ORGANIZER ----------------
else:
    st.title("📋 Organizer")
    password = st.text_input("Organizer password", type="password")
    if password != os.getenv("ORGANIZER_PASSWORD", "changeme"):
        st.info("Enter the organizer password to continue.")
    else:
        players = get_all_players()
        st.write(f"**{len(players)}** players registered.")
        if st.button("Prepare PDF", type="primary"):
            with st.spinner("Building PDF..."):
                st.session_state.pdf = build_pdf(players, "Player Book")
        if st.session_state.get("pdf"):
            st.download_button(
                "⬇️ Download PDF",
                data=st.session_state.pdf,
                file_name="player_book.pdf",
                mime="application/pdf",
            )