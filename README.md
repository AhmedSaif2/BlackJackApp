# Blackjack Game 🃏

A Python implementation of the classic Blackjack game, with a graphical interface built on Tkinter and a console mode. The game logic is kept separate from both front-ends, and the project has no third-party dependencies.

## Features
- **User-Friendly Interface**: A simple and intuitive GUI for playing Blackjack, with real playing-card images that slide in from the deck and flip face up as they are dealt.
- **AI Dealer**: The computer player's hit/stand decisions are made by [Jev](https://www.datacamp.com/blog/system-one-models-jev), with a built-in rule-based fallback.
- **Flexible Ace Handling**: Ace values adapt dynamically to provide the best possible hand.
- **One-Screen Table**: The game opens straight on the table, with no sign-up or name prompt. You bet, play and see the result in one place. Results appear in a banner instead of pop-ups, and the last hand stays on the table until your next bet.
- **Keyboard Play**: `1` / `2` / `3` bet 10$ / 50$ / 200$, `Enter` repeats your last bet, `H` hits and `S` stands.
- **Saved Progress**: Your chips and stats are saved automatically and picked up next time, in both the GUI and the console. Your bet is saved as soon as it's placed, so closing the game mid-hand doesn't undo a losing hand.
- **Scoreboard**: Rounds played, wins, losses, draws, win rate, blackjacks, busts, net winnings and the most chips you've held.
- **Start Over Anytime**: Out of chips, or just want a clean slate? "New game" resets your chips and stats.
- **Console Mode**: Play the same game in the terminal with `--cli`.

## How to Play
1. Launch the game. You start with 2500$ in chips, or wherever you left off last time.
2. Place a bet: 10$, 50$ or 200$ (or press `1`, `2`, `3`).
3. Play your hand:
   - "Hit" (`H`) draws another card.
   - "Stand" (`S`) passes the turn to the dealer.
4. The dealer plays its hand (decided by Jev), revealing its cards one by one.
5. The result shows on the table. A win pays double your bet, and a draw returns it. Bet again, or press `Enter` to repeat your last bet.

## Requirements
- Python 3.9 or newer, with Tkinter (included with the standard Python installers for Windows and macOS; on Debian/Ubuntu install `python3-tk`).

## Installation & Running
1. Clone the repository:
   ```bash
   git clone https://github.com/AhmedSaif2/BlackJackApp.git
   cd BlackJackApp
   ```
2. Run the game straight from the source tree:
   ```bash
   python -m blackjack          # GUI
   python -m blackjack --cli    # console
   ```
   Or install it to get a `blackjack` command:
   ```bash
   pip install .
   blackjack
   ```

## Saved Progress
Your chips and stats are kept in a small JSON file:

| Platform | Location |
| --- | --- |
| Windows | `%APPDATA%\BlackjackApp\save.json` |
| macOS | `~/Library/Application Support/BlackjackApp/save.json` |
| Linux | `$XDG_CONFIG_HOME/BlackjackApp/save.json` (default `~/.config/...`) |

Set `BLACKJACK_SAVE_FILE` to use a different file. Delete the file, or click "New game", to start over. If the file is missing or unreadable, the game starts fresh.

## Computer Player (Jev)
The dealer is driven by Jev, TypeSafe AI's System One model. On every turn the dealer sends Jev its cards, its total and the player's final total as a `choice` question (`hit` / `stand`) and plays whatever Jev picks.

Configure it with environment variables before starting the game:

| Variable | Default | Purpose |
|---|---|---|
| `JEV_API_KEY` (or `TYPESAFE_API_KEY`) | — | API key. If it is not set, Jev is disabled |
| `JEV_API_URL` | `https://api.typesafe.ai/v1/systemone` | Endpoint (point this at a proxy such as OmniaKey if needed) |
| `JEV_MODEL` | `jev-latest` | Model id |

If Jev isn't configured, doesn't answer within 3 seconds, or returns something unexpected, the dealer falls back to its built-in rules: always hit at 14 or less, always stand at 19 or more, and flip a coin in between. In the GUI the request runs on a background thread, so the window stays responsive while Jev decides. The tests never call the real API.

## Running the Tests
```bash
python -m unittest discover
```
The GUI tests drive the real Tkinter widgets and are skipped automatically when no display is available.

## Project Structure
```
blackjack/
├── cards.py         # Suit, Card and Deck
├── hand.py          # Hand: totals, flexible aces, bust / 21 checks
├── participants.py  # Player (pocket money, bets) and Dealer (deals cards, asks Jev to hit/stand)
├── jev.py           # Client for the Jev API (standard library only)
├── game.py          # Round: one hand of blackjack, shared by both front-ends
├── stats.py         # PlayerStats: the scoreboard, updated when a round ends
├── save.py          # SaveFile: keeps your chips and stats between sessions
├── gui.py           # Tkinter app: a single table screen
├── cli.py           # Console front-end
├── __main__.py      # Entry point (`python -m blackjack [--cli]`)
└── assets/playing_cards/  # Card images
tests/               # Unit tests for the game logic, the console and the GUI
```

## Code Highlights
- **Ace Handling**: Flexible Ace logic ensures optimal hand value without exceeding 21.
- **UI-independent game logic**: `Round` steps through a hand (`hit`, `stand`, `dealer_step`) without any I/O, so the GUI and console share exactly the same rules.
- **Page Navigation**: Each screen is a Tkinter frame; the app swaps pages through callbacks.
- **Dynamic Gameplay**: Dealer's cards are revealed one by one to enhance realism.

## Technologies Used
- **Programming Language**: Python
- **GUI**: Tkinter (standard library)

## Screenshots
- **Winning a round:**

![Wining](https://github.com/user-attachments/assets/dbc70654-d099-4a19-924d-a57c06eb07cb)

- **Losing a round:**

![Losing](https://github.com/user-attachments/assets/27aafc93-740d-448e-ae19-5fff52af7413)

- **Hitting a blackjack:**

![Blackjack](https://github.com/user-attachments/assets/1c80f4eb-5cdb-4e70-9fb2-c4a4de72b481)

> These screenshots are from the original Windows Forms version; the Python GUI keeps the same screens and layout.

## Future Enhancements
- Improve the UI with custom graphics or themes.
- Implement additional game features like splitting or doubling down.
- Pay 3:2 on a natural blackjack and give the dealer a hole card, as in casino rules.
