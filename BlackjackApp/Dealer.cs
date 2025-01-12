using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace BlackjackApp
{
    public class Dealer : Participant
    {
        public Dealer() : base()
        {
            Name = "The Dealer"; 
        }

        public void DealCard(DeckOfCards deck,Participant player)
        {
            Card card = deck.NextCard();
            deck.RemoveCard(card);
            player.AddCard(card);
        }
        public override int MakeChoice()
        {
            int handSum = CurrentHand.GetSum();
            if (handSum <= 14)
            {
                return 1;
            }
            else if (handSum >= 19)
            {
                return 2;
            }
            else
            {
                Random random = new Random();
                return random.Next(1,3);
            }
        }
    }
}
