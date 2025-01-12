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
        public BlackjackGame(Dealer dealer,Player player)
        {
            Dealer = dealer;
            Player = player;

            Player.ResetHand();
            Dealer.ResetHand();

            Deck=new DeckOfCards();
            Deck.ShuffleDeck();

            Console.WriteLine(" -------------------------- Player's turn --------------------------");
            Console.WriteLine("Current Pocket Money = " + Player.GetPocketMoney());
            Console.WriteLine("Place a bet");

            int bet = Convert.ToInt32(Console.ReadLine());
            while (!Player.PlaceBet(bet))
            {
                Console.WriteLine("Please Enter a valid amount");
                bet=Convert.ToInt32(Console.ReadLine());
            }
            
            // Player's Turn 
            int PlayerScore = GetTurnScore(Player);
            if (PlayerScore > 21)
            {
                Console.WriteLine("You Lost!");
                return;
            }

            Console.WriteLine(" -------------------------- Dealer's turn --------------------------");

            int DealerScore = GetTurnScore(Dealer);
            // Dealer's Turn 

            if (DealerScore > 21 || PlayerScore > DealerScore)
            {
                Console.WriteLine(Player.GetName()+" Won !");
                Player.AddToPocketMoney(bet*2);
            }
            else if (PlayerScore == DealerScore)
            {
                Console.WriteLine("Draw!");
                Player.AddToPocketMoney(bet);
            }
            else
            {
                Console.WriteLine(Dealer.GetName() + " Won !");

            }
        }
        private int GetTurnScore(Participant participant)
        {
            Dealer.DealCard(Deck, participant);
            Dealer.DealCard(Deck, participant);
            // Player's Turn 
            while (true)
            {
                participant.SeeHand();
                if (participant.CurrentHand.IsBlackJack())
                {
                    Console.WriteLine("Blackjack!");
                    break;
                }
                if (participant.CurrentHand.IsBust())
                {
                    break;
                }
                int choice = participant.MakeChoice();
                if (choice == 1)
                {
                    Dealer.DealCard(Deck, participant);
                }
                else if (choice == 2)
                {
                    break;
                }
                Thread.Sleep(2000);

            }
            return participant.CurrentHand.GetSum(); 
        }
    }
}
