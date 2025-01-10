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
        public BlackjackGame()
        {
            Dealer = new Dealer();
            Console.WriteLine("Please Enter Your Name: ");
            string PlayerName=Console.ReadLine();
            Player = new Player(PlayerName,100);

            DeckOfCards deck=new DeckOfCards();
            deck.ShuffleDeck();

            Dealer.DealCard(deck,Player);
            Dealer.DealCard(deck,Player);
            // Player's Turn 
            while (true)
            {
                Player.SeeHand();
                if (Player.CurrentHand.IsBlackJack())
                {
                    Console.WriteLine("Blackjack!");
                    break;
                }
                if (!Player.CurrentHand.IsValidHand())
                {
                    break;
                }
                Console.WriteLine("Type 1 to Hit Or 2 To Stand");
                int choice=Player.MakeChoice();
                if (choice == 1)
                {
                    Dealer.DealCard(deck,Player);
                }
                else if (choice == 2)
                {
                    break;
                }
            }
            int PlayerScore = Player.CurrentHand.GetSum();
            if (PlayerScore > 21)
            {
                Console.WriteLine("You Lost!");
                return;
            }

            // Dealer's Turn 
            Dealer.DealCard(deck, Dealer);
            Dealer.DealCard(deck, Dealer);
            while (true)
            {
                Dealer.SeeHand();
                if (Dealer.CurrentHand.IsBlackJack())
                {
                    Console.WriteLine("Blackjack!");
                    break;
                }
                if (!Dealer.CurrentHand.IsValidHand())
                {
                    break;
                }
                int choice = Dealer.MakeChoice();
                if (choice == 1)
                {
                    Dealer.DealCard(deck, Dealer);
                }
                else if (choice == 2)
                {
                    break;
                }
            }

            if (Dealer.CurrentHand.GetSum()>21||Player.CurrentHand.GetSum()>Dealer.CurrentHand.GetSum())
            {
                Console.WriteLine(Player.Name+" Won !");
            }
            else if (Player.CurrentHand.GetSum() == Dealer.CurrentHand.GetSum())
            {
                Console.WriteLine("Draw!");
            }
            else
            {
                Console.WriteLine("The Dealer Won !");
            }
        }
    }
}
