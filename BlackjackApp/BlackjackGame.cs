using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace BlackjackApp
{
    public class BlackjackGame
    {
        private Dealer Dealer;
        private Player Player;
        private DeckOfCards Deck;
        public BlackjackGame()
        {
            Dealer = new Dealer();
            Console.WriteLine("Please Enter Your Name: ");
            string PlayerName=Console.ReadLine();
            Player = new Player(PlayerName,100);

            Deck=new DeckOfCards();
            Deck.ShuffleDeck();

            // Player's Turn 
            int PlayerScore = GetTurnScore(Player);
            if (PlayerScore > 21)
            {
                Console.WriteLine("You Lost!");
                return;
            }

            int DealerScore = GetTurnScore(Dealer);
            // Dealer's Turn 

            if (DealerScore > 21 || PlayerScore > DealerScore)
            {
                Console.WriteLine(Player.Name+" Won !");
            }
            else if (PlayerScore == DealerScore)
            {
                Console.WriteLine("Draw!");
            }
            else
            {
                Console.WriteLine("The Dealer Won !");
            }
        }
        private int GetTurnScore(Player player)
        {
            Dealer.DealCard(Deck, player);
            Dealer.DealCard(Deck, player);
            // Player's Turn 
            while (true)
            {
                player.SeeHand();
                if (player.CurrentHand.IsBlackJack())
                {
                    Console.WriteLine("Blackjack!");
                    break;
                }
                if (!player.CurrentHand.IsValidHand())
                {
                    break;
                }
                int choice = player.MakeChoice();
                if (choice == 1)
                {
                    Dealer.DealCard(Deck, player);
                }
                else if (choice == 2)
                {
                    break;
                }
            }
            return player.CurrentHand.GetSum(); 
        }
    }
}
