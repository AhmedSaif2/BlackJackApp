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
        private int AceCount;
        public Hand() { 
            Cards = new List<Card>();
            Sum = 0;
            AceCount = 0;
        }
        public void AddCard(Card card)
        {
            Cards.Add(card);
            if (card.Value == 11)
            {
                AceCount++;
            }
            Sum += card.Value;
            if (Sum > 21 &&AceCount > 0)
            {
                AceCount--;
                Sum -= 10;
            }
        }
        public int GetSum()
        {
            return Sum;
        }
        public bool IsBlackJack()
        {
            return Sum == 21;
        }
        public bool IsBust()
        {
            return Sum > 21;
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
