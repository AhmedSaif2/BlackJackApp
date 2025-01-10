using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace BlackjackApp
{
    internal class Hand
    {
        private List<Card> Cards;
        private int sum;
        public Hand() { 
            Cards = new List<Card>();
            sum = 0;
        }
        public void AddCard(Card card)
        {
            Cards.Add(card);
            sum += card.Value;
        }
        public void ShowHand()
        {
            foreach (Card card in Cards)
            {
                Console.WriteLine(card);
            }
            Console.WriteLine("Current Sum = "+ getSum());
        }
        public int getSum()
        {
            return sum;
        }
        public bool IsValidHand()
        {
            return sum <= 21;
        }
    }
}
