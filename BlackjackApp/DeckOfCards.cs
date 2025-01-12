using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace BlackjackApp
{
    public class DeckOfCards
    {
        private List<Card> Cards;

        public DeckOfCards()
        {
            Cards = new List<Card>();
            for (int i = 2; i <= 10; i++)
            {
                string rank=i.ToString();
                Helper.AddAllSuits(Cards, rank);
            }
            Helper.AddAllSuits(Cards, "jack");
            Helper.AddAllSuits(Cards, "queen");
            Helper.AddAllSuits(Cards, "king");
            Helper.AddAllSuits(Cards, "Ace");
        }
        public void ShuffleDeck()
        {
            Random random= new Random();
            int listSize = Cards.Count;
            for (int i=0;i<listSize; i++)
            {
                int Index=random.Next(0, listSize);

                Card tmp = Cards[Index];
                Cards[Index] = Cards[i];
                Cards[i] = tmp;
            }
        }
        public Card NextCard()
        {
            Card card = Cards.Last();
            return card;
        }
        public void ShowDeck()
        {
            foreach (Card card in Cards)
            {
                Console.WriteLine(card);
            }
        }

        public void RemoveCard(Card card)
        {
            Cards.Remove(card);
        }
    }
}
