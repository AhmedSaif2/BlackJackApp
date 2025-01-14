# Blackjack Game 🃏

A C# implementation of the classic Blackjack game, featuring a graphical user interface using Windows Forms. This project demonstrates OOP principles and SOLID design patterns, with a focus on user interaction and smooth gameplay.

## Features
- **User-Friendly Interface**: A simple and intuitive GUI for playing Blackjack.
- **Dynamic Dealer Logic**: Dealer actions (hit or stand) are fully automated based on game rules.
- **Flexible Ace Handling**: Ace values adapt dynamically to provide the best possible hand.
- **Interactive Gameplay**:
  - Players can enter their name and place bets.
  - Real-time updates to the player's and dealer's cards and scores.
- **Modular Design**: Pages like the betting screen and game screen are implemented as user controls for easy navigation.


## How to Play
1. Enter your name on the main screen and click "Play".
2. Place your bet on the betting screen.
3. Play your hand:
   - Click "Hit" to draw another card.
   - Click "Stand" to pass the turn to the dealer.
4. The dealer plays its hand based on predefined rules.
5. See the results and play again!

## Project Structure
- **Core Logic**: Handles Blackjack game rules, including Ace value adjustments and dealer/player logic.
- **GUI**: Built using Windows Forms for a clean and responsive user experience.
- **Events and Delegates**: Used to navigate between different pages (e.g., main screen to betting screen) and trigger gameplay events.

## Code Highlights
- **Ace Handling**: Flexible Ace logic ensures optimal hand value without exceeding 21.
- **Page Navigation**: Implements user controls and event-driven programming for seamless transitions between screens.
- **Dynamic Gameplay**: Dealer's cards are revealed one by one to enhance realism.

## Technologies Used
- **Programming Language**: C#
- **Framework**: .NET Windows Forms
- **IDE**: Visual Studio 2022
  
## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/AhmedSaif2/BlackjackGame.git
   ```
2. Open the project in Visual Studio.
3. Build and run the solution.

## Screenshots
- **Winning a round:**

![Wining](https://github.com/user-attachments/assets/dbc70654-d099-4a19-924d-a57c06eb07cb)

- **Losing a round:**

![Losing](https://github.com/user-attachments/assets/27aafc93-740d-448e-ae19-5fff52af7413)

- **Hitting a blackjack:**

![Blackjack](https://github.com/user-attachments/assets/1c80f4eb-5cdb-4e70-9fb2-c4a4de72b481)

## Future Enhancements
- Add animations for card dealing.
- Improve the UI with custom graphics or themes.
- Implement additional game features like splitting or doubling down.
- Add a scoreboard to track player stats.
