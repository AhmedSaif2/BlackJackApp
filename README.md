# Blackjack Game 🃏

A Python implementation of the classic Blackjack game, with a graphical interface built on Tkinter and a console mode. The game logic is kept separate from both front-ends, and the project has no third-party dependencies.

## Features
- **User-Friendly Interface**: A simple and intuitive GUI for playing Blackjack, with real playing-card images that slide in from the deck and flip face up as they are dealt.
- **AI Dealer**: The computer player's hit/stand decisions are made by [Jev](https://www.datacamp.com/blog/system-one-models-jev), with a built-in rule-based fallback.
- **Flexible Ace Handling**: Ace values adapt dynamically to provide the best possible hand.
- **Interactive Gameplay**:
  - Players can enter their name and place bets (bets you can't afford are disabled).
  - Real-time updates to the player's and dealer's cards and scores.
  - When you run out of money you can start over.
- **Scoreboard**: Session stats are tracked for each player: rounds played, wins, losses, draws, win rate, blackjacks, busts, net winnings and the highest pocket money reached. They appear on the betting screen after the first round, and in the console after every round and in the closing summary.
- **Console Mode**: Play the same game in the terminal with `--cli`.

## How to Play
1. Enter your name on the main screen and click "Play".
2. Place your bet on the betting screen (10$, 50$ or 200$; you start with 2500$).
3. Play your hand:
   - Click "Hit" to draw another card.
   - Click "Stand" to pass the turn to the dealer.
4. The dealer plays its hand (decided by Jev), revealing its cards one by one.
5. See the results and play again! A win pays double your bet, a draw returns it.

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
├── stats.py         # PlayerStats: the session scoreboard, updated when a round ends
├── gui.py           # Tkinter app: welcome, betting and game pages
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
- Save player stats between sessions and add a leaderboard across players.
