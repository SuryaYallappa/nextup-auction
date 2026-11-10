# Nextup

Player registration, a printable player book, and a live draw screen for local cricket and kabaddi auctions.

Local tournaments usually run their player lists on paper, WhatsApp, or Excel. On auction day the organizer pulls a numbered chit from a bowl and has to find that player in a pile of papers. Nextup replaces that: players register from their phones, the organizer gets a clean PDF player book, and on the day, typing a chit number puts that player's card on the projector.

Bidding and money stay in the room. The app only handles the player side.

> **Live demo:** _coming soon_
>
> **Status:** version 1 works end to end on a local network. Cloud deployment is the next step.

## Screenshots

<!-- Add your screenshots to a /screenshots folder and update these paths -->

| Phone registration | Public tournament board |
|---|---|
| ![Registration form](screenshots\register.png) | ![Public board](screenshots\Public.png) |

| Organizer view with duplicate flags | Projector card |
|---|---|
| ![Organizer](screenshots\oraganizer.png) | ![Projector](screenshots\auction.png) |

## Features

**For players**
- Public home page listing tournaments that are open for registration
- Registration from any phone: name, role, age, village, phone number, photo
- Age range and deadline checks, with clear messages when a player is not eligible
- Each player gets a number that restarts at 1 in every tournament

**For the organizer** (password protected, at `/?page=organizer`)
- Create tournaments with a sport, event date, age range, registration deadline, and public or private visibility
- A unique registration link for every tournament, sent to players on WhatsApp
- Open or close registration manually, on top of the automatic deadline
- Edit tournament settings and player details, including photos
- Possible duplicates are flagged for review when two entries share a phone number or a name
- Remove a player safely: they are hidden but kept, so they can be restored, and their number is never reused
- Download a PDF player book with photo, number, name, role, age, village, and optionally phone number

**On auction day**
- Type the number from the chit and the player's card appears full screen for the projector (photo, name, role, age, village)
- Warns when a number does not exist or was already shown
- Phone numbers never appear on the projector or on the public pages

## How it works

- **Registration links.** Each tournament gets a random 6-character code, and its link looks like `/?t=ab12cd`. The page the visitor sees is chosen from the address: `?t=` opens that tournament's form, `?page=organizer` opens the login, and the bare address opens the public board.
- **Player numbers.** Numbers are assigned inside a database transaction that locks writes, so two people registering at the same moment can never receive the same number.
- **Duplicates are flagged, never decided.** Names are compared after lowercasing and removing extra spaces and dots. The organizer reviews each group and can edit, remove, or mark it as not a duplicate. Nothing is deleted automatically.
- **Soft remove.** Removed players keep their row, photo, and number. Chits already written stay valid, and a removal can be undone.
- **Photos** are resized to at most 800 px and corrected for phone rotation, so the PDF stays small.
- **Deadlines use Indian time**, even if the server runs in another timezone.

## Tech stack

- Python 3
- [Streamlit](https://streamlit.io) for the web interface
- SQLite for storage
- Pillow for image processing
- fpdf2 for the PDF player book

## Run it locally

Requires Python 3.10 or newer.

```bash
git clone https://github.com/SuryaYallappa/nextup-auction.git
cd nextup-auction

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
streamlit run app.py
```

Then open:

| Who | Address |
|---|---|
| Players | `http://localhost:8501` |
| Organizer | `http://localhost:8501/?page=organizer` |

### Configuration

Set these as environment variables before starting the app:

| Variable | Purpose | Default |
|---|---|---|
| `ORGANIZER_PASSWORD` | Organizer login password | `changeme` |
| `BASE_URL` | Address used when building registration links | `http://localhost:8501` |

**Change the default password before using the app with real players.**

PowerShell example, with the app reachable from phones on the same Wi-Fi (use the Network URL Streamlit prints on startup):

```powershell
$env:ORGANIZER_PASSWORD="choose-a-strong-password"
$env:BASE_URL="http://192.168.1.10:8501"
streamlit run app.py
```

## Project structure

```
app.py            Streamlit pages: public board, registration, organizer, draw screen
db.py             SQLite storage: tournaments, players, photos
validators.py     Phone cleaning, age check, registration deadline check
duplicates.py     Duplicate detection (same phone or same name)
pdf_book.py       PDF player book generation
test_validators.py
test_duplicates.py
requirements.txt
```

`db.py`, `validators.py`, `duplicates.py`, and `pdf_book.py` do not depend on Streamlit, so the logic can be tested on its own.

## Tests

```bash
python test_validators.py
python test_duplicates.py
```

## Known limitations

- Age is self-declared and cannot be verified by the app. The organizer checks ages at the ground.
- The PDF uses built-in fonts, so names in Devanagari, Kannada, and other non-Latin scripts show as `?`. Adding a Unicode font is planned.
- Data and photos are stored on the machine running the app. Hosting that resets its disk would erase them, so deployment needs persistent storage.

## Roadmap

- [x] Registration, tournaments, public board, organizer login
- [x] Duplicate flags with edit, remove, and restore
- [x] PDF player book
- [x] Live draw screen
- [ ] Deployment with persistent storage
- [ ] Docker image
- [ ] GitHub Actions workflow that runs the tests on every push
- [ ] Unicode font support in the PDF
- [ ] Backup of the player book and photos to cloud storage
