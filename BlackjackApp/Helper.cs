using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace BlackjackApp
{
    public class Helper
    {
        public enum Suit
        {
            Heart,
            Diamond,
            Club,
            Spade
        }
        public static void AddAllSuits(List<Card> cards,string rank) 
        {
            cards.Add(new Card(rank, Helper.Suit.Heart));
            cards.Add(new Card(rank, Helper.Suit.Diamond));
            cards.Add(new Card(rank, Helper.Suit.Spade));
            cards.Add(new Card(rank, Helper.Suit.Club));
        }
    }
}
