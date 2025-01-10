using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace BlackjackApp
{
    public class Dealer : Player
    {
        public Dealer() : base()
        {
            Name = "Dealer"; 
        }

        public void DealCard(DeckOfCards deck,Player player)
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
