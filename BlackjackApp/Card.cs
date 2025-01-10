using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace BlackjackApp
{
    internal class Card
    {
        private string Rank { get; set; }
        public Helper.Suit Suit { get; set; }
        public int Value { get; }
        public Card(string rank, Helper.Suit suit)
        {
            Rank = rank;
            Suit = suit;
            if (Rank.Length == 1 && Rank[0] >= '1' && Rank[0] <= '9') 
            {
                Value = Rank[0] - '0';
            }
            else if (Rank == "10" || Rank.ToLower() == "jack" || Rank.ToLower() == "queen" || Rank.ToLower() == "king") 
            {
                Value = 10;
            }
            else
            {
                throw new Exception("Invalid Card Rank!");
            }
        }
        public override string ToString()
        {
            return Rank + " Of " + Suit+" = "+Value.ToString(); 
        }
    }
}
