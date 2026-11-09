import os
import streamlit as st
from validators import clean_phone, check_age, check_registration_open, today_in_india
from db import (
    init_db, create_tournament, get_tournament_by_code, list_tournaments,
    list_public_tournaments, set_registration_open, add_player, get_player,
    get_all_players, count_players,
)
from pdf_book import build_pdf

init_db()
st.set_page_config(page_title="Nextup", page_icon="🏏", layout="wide")

ROLES_BY_SPORT = {
    "Cricket": ["Batsman", "Bowler", "All-rounder", "Wicketkeeper"],
    "Kabaddi": ["Raider", "Defender", "All-rounder"],
}
BASE_URL = os.getenv("BASE_URL", "http://localhost:8501")
ORGANIZER_PASSWORD = os.getenv("ORGANIZER_PASSWORD", "changeme")


# ================= PLAYER VIEW (opened from the registration link) =================
def registration_page(t):
    if t is None:
        st.error("This registration link is not valid.")
        return
    st.title(f"🏏 {t['name']}")
    st.caption(f"{t['sport']} · {t['event_date']} · Ages {t['min_age']} to {t['max_age']}")

    closed = check_registration_open(
        t["registration_open"], t["registration_deadline"], today_in_india()
    )
    if closed:
        st.warning(closed)
        return

    # After a successful registration, show the number instead of the form
    done_key = f"done_{t['code']}"
    if st.session_state.get(done_key):
        st.success(f"Registered! Your player number is {st.session_state[done_key]}. Remember it.")
        if st.button("Register another player"):
            del st.session_state[done_key]
            st.rerun()
        return

    if t["registration_deadline"]:
        st.info(f"Register by {t['registration_deadline']}.")

    with st.form("register"):
        name = st.text_input("Full name")
        role = st.selectbox("Role", ROLES_BY_SPORT[t["sport"]])
        age = st.number_input("Age", min_value=5, max_value=100, value=20)
        village = st.text_input("Village")
        phone_raw = st.text_input("Phone number")
        photo = st.file_uploader("Your photo", type=["jpg", "jpeg", "png"])
        submitted = st.form_submit_button("Register", type="primary")

    if submitted:
        phone = clean_phone(phone_raw)
        age_error = check_age(int(age), t["min_age"], t["max_age"])
        if not name.strip() or not village.strip() or photo is None:
            st.error("Please fill every field and upload a photo.")
        elif phone is None:
            st.error("Enter a valid 10-digit mobile number.")
        elif age_error:
            st.error(age_error)
        else:
            try:
                number = add_player(
                    t["id"], name.strip(), role, int(age),
                    village.strip(), phone, photo.getvalue(),
                )
            except Exception as e:
                st.error(f"Could not save your registration. Try a different photo. ({e})")
            else:
                st.session_state[done_key] = number
                st.rerun()


# ================= ORGANIZER LOGIN =================
def organizer_gate():
    if st.session_state.get("is_organizer"):
        return
    st.title("📋 Nextup Organizer")
    with st.form("login"):
        pw = st.text_input("Organizer password", type="password")
        ok = st.form_submit_button("Log in", type="primary")
    if ok:
        if pw == ORGANIZER_PASSWORD:
            st.session_state.is_organizer = True
            st.rerun()
        else:
            st.error("Wrong password.")
    st.stop()


# ================= ORGANIZER: MANAGE =================
def create_form(has_tournaments):
    with st.expander("➕ Create a new tournament", expanded=not has_tournaments):
        with st.form("create"):
            name = st.text_input("Tournament name")
            sport = st.selectbox("Sport", list(ROLES_BY_SPORT))
            event_date = st.date_input("Event date")
            col1, col2 = st.columns(2)
            min_age = col1.number_input("Minimum age", min_value=5, max_value=80, value=16)
            max_age = col2.number_input("Maximum age", min_value=5, max_value=80, value=35)
            deadline = st.date_input("Registration deadline", value=today_in_india())
            is_public = st.checkbox("Show on the public tournament board")
            create = st.form_submit_button("Create tournament", type="primary")
        if create:
            if not name.strip():
                st.error("Enter a tournament name.")
            elif min_age > max_age:
                st.error("Minimum age cannot be higher than maximum age.")
            elif deadline > event_date:
                st.error("The deadline must be on or before the event date.")
            else:
                code = create_tournament(
                    name.strip(), sport, event_date.isoformat(),
                    int(min_age), int(max_age), deadline.isoformat(), is_public,
                )
                st.session_state.pending_select = code
                st.rerun()


def manage_page(t):
    st.title(f"📋 {t['name']}")
    st.caption(
        f"{t['sport']} · {t['event_date']} · Ages {t['min_age']} to {t['max_age']} · "
        f"Deadline {t['registration_deadline']} · "
        + ("Public" if t["is_public"] else "Private")
    )

    st.markdown("**Registration link (send this to players):**")
    st.code(f"{BASE_URL}/?t={t['code']}", language=None)

    is_open = st.toggle(
        "Registration open",
        value=bool(t["registration_open"]),
        key=f"open_{t['code']}",
    )
    if is_open != bool(t["registration_open"]):
        set_registration_open(t["id"], is_open)
        st.rerun()

    players = get_all_players(t["id"])
    st.subheader(f"{len(players)} players registered")
    if players:
        st.dataframe(
            [
                {"No.": p["number"], "Name": p["name"], "Role": p["role"],
                 "Age": p["age"], "Village": p["village"], "Phone": p["phone"]}
                for p in players
            ],
            hide_index=True,
        )

    pdf_key = f"pdf_{t['code']}"
    if st.button("Prepare PDF", type="primary"):
        with st.spinner("Building PDF..."):
            st.session_state[pdf_key] = build_pdf(players, t["name"])
    if st.session_state.get(pdf_key):
        st.download_button(
            "⬇️ Download PDF",
            data=st.session_state[pdf_key],
            file_name=f"{t['code']}_player_book.pdf",
            mime="application/pdf",
        )
        st.caption("New registrations since you prepared this? Click Prepare PDF again.")


# ================= ORGANIZER: AUCTION (projector) =================
def auction_page(t):
    drawn_key, current_key = f"drawn_{t['code']}", f"current_{t['code']}"
    if drawn_key not in st.session_state:
        st.session_state[drawn_key] = []
    drawn = st.session_state[drawn_key]

    st.sidebar.markdown(f"**Registered players:** {count_players(t['id'])}")
    with st.sidebar.form("draw"):
        number = st.number_input("Number from the chit", min_value=1, step=1, value=1)
        show = st.form_submit_button("Show player", type="primary")

    if show:
        player = get_player(t["id"], int(number))
        if player is None:
            st.sidebar.error(f"No player with number {int(number)}.")
        else:
            if player["number"] in drawn:
                st.sidebar.warning("This number was already shown.")
            else:
                drawn.append(player["number"])
            st.session_state[current_key] = player

    st.sidebar.markdown("**Shown so far:** " + (", ".join(map(str, drawn)) or "none"))

    p = st.session_state.get(current_key)
    if p is None:
        st.markdown("<h1 style='text-align:center;margin-top:30vh'>Nextup 🏏</h1>",
                    unsafe_allow_html=True)
    else:
        st.markdown(
            f"<h1 style='text-align:center;font-size:90px;margin:0'>Player #{p['number']}</h1>",
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

# ================= PUBLIC HOME BOARD =================
def home_page():
    st.title("🏏 Nextup")
    st.subheader("Tournaments open for registration")

    today = today_in_india()
    open_ones = [
        x for x in list_public_tournaments()
        if check_registration_open(x["registration_open"], x["registration_deadline"], today) is None
    ]
    if not open_ones:
        st.info("No tournaments are open for registration right now. Check back soon.")
        return

    for x in open_ones:
        with st.container(border=True):
            st.markdown(f"### {x['name']}")
            st.write(f"{x['sport']} · {x['event_date']} · Ages {x['min_age']} to {x['max_age']}")
            if x["registration_deadline"]:
                st.caption(f"Register by {x['registration_deadline']}")
            if st.button("Register", key=f"reg_{x['code']}", type="primary"):
                st.query_params["t"] = x["code"]
                st.rerun()


# ================= ROUTING =================
code = st.query_params.get("t")
if code:                                   # a player opened a registration link
    if st.button("← All tournaments"):
        st.query_params.clear()
        st.rerun()
    registration_page(get_tournament_by_code(code))
    st.stop()

if st.query_params.get("page") != "organizer":   # the public home board
    home_page()
    st.stop()

organizer_gate()                           # only the organizer address needs the password                         # everyone else must log in

tournaments = list_tournaments()
names = {x["code"]: f"{x['name']} ({x['sport']})" for x in tournaments}

# After creating a tournament, select it (must happen before the selectbox is drawn)
if "pending_select" in st.session_state:
    st.session_state.selected = st.session_state.pop("pending_select")

st.sidebar.title("Nextup")
selected_code = None
if tournaments:
    selected_code = st.sidebar.selectbox(
        "Tournament", list(names), format_func=names.get, key="selected"
    )
page = st.sidebar.radio("Page", ["Manage", "Auction"])
t = get_tournament_by_code(selected_code) if selected_code else None

if page == "Manage":
    create_form(has_tournaments=bool(tournaments))
    if t:
        manage_page(t)
    else:
        st.info("Create your first tournament above.")
else:
    if t:
        auction_page(t)
    else:
        st.info("Create a tournament first (Manage page).")