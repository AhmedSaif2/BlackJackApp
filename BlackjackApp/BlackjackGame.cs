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
        private int Bet;
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
                Player.AddToPocketMoney(Bet * 2);
            }
            else if (PlayerScore == DealerScore)
            {
                Console.WriteLine("Draw!");
                Player.AddToPocketMoney(Bet);
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
        public void SetBet(int bet)
        {
            Bet = bet;
        }
    }
}
