import os
from fpdf import FPDF

CARD_W, CARD_H = 92, 62
GAP_X, GAP_Y = 6, 4
START_X, START_Y = 10, 26
COLS, ROWS = 2, 4  # 8 players per A4 page


def safe(text):
    """Built-in PDF fonts only support Latin characters, so replace others with '?'."""
    return str(text).encode("latin-1", "replace").decode("latin-1")


def build_pdf(players, title="Player Book", show_phone=True):
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    per_page = COLS * ROWS

    for i, p in enumerate(players):
        slot = i % per_page
        if slot == 0:  # start a new page every 8 players
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 18)
            pdf.set_xy(10, 10)
            pdf.cell(190, 10, safe(title), align="C")

        col, row = slot % COLS, slot // COLS
        x = START_X + col * (CARD_W + GAP_X)
        y = START_Y + row * (CARD_H + GAP_Y)

        pdf.rect(x, y, CARD_W, CARD_H)  # card border

        # photo on the left
        if p["photo_path"] and os.path.exists(p["photo_path"]):
            pdf.image(p["photo_path"], x + 3, y + 3, 34, 46, keep_aspect_ratio=True)

        # player number under the photo
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_xy(x + 3, y + 51)
        pdf.cell(34, 8, f"#{p['number']}", align="C")

        # details on the right
        tx, tw = x + 40, CARD_W - 43
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_xy(tx, y + 5)
        pdf.multi_cell(tw, 6, safe(p["name"]))

        pdf.set_font("Helvetica", "", 10)
        pdf.set_xy(tx, y + 22)
        pdf.cell(tw, 6, safe(f"Role: {p['role']}"))
        pdf.set_xy(tx, y + 28)
        pdf.cell(tw, 6, f"Age: {p['age']}")
        pdf.set_xy(tx, y + 34)
        pdf.multi_cell(tw, 5.5, safe(f"Village: {p['village']}"))

        if show_phone:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_xy(tx, y + 50)
            pdf.cell(tw, 7, safe(f"Ph: {p['phone']}"))

    if not players:
        pdf.add_page()
        pdf.set_font("Helvetica", "", 14)
        pdf.cell(0, 10, "No players registered yet.")

    return bytes(pdf.output())