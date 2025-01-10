using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace BlackjackApp
{
    public class Hand
    {
        private List<Card> Cards;
        private int Sum;
        public Hand() { 
            Cards = new List<Card>();
            Sum = 0;
        }
        public void AddCard(Card card)
        {
            Cards.Add(card);
            Sum += card.Value;
        }
        public int GetSum()
        {
            return Sum;
        }
        public bool IsBlackJack()
        {
            return Sum == 21;
        }
        public bool IsValidHand()
        {
            return Sum <= 21;
        }
        public void ShowHand()
        {
            foreach (Card card in Cards)
            {
                Console.WriteLine(card);
            }
            Console.WriteLine("Current Sum = "+ GetSum());
        }

    }
}
