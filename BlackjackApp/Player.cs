using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace BlackjackApp
{
    public class Player
    {
        public string Name { get; set; }
        public Hand CurrentHand { get; set; }
        public int Bet { get; set; }
        //public int PocketMoney { get; set; }
        public Player() { 
            CurrentHand = new Hand();
        }
        public Player(string name,int bet) { 
            Name= name;
            Bet= bet;
            CurrentHand=new Hand();
        }
        public void SeeHand()
        {
            CurrentHand.ShowHand();
        }
        public virtual int MakeChoice()
        {
            // 1 for Hit
            // 2 for Stand
            Console.WriteLine("Type 1 to Hit Or 2 To Stand");
            string choice = Console.ReadLine();
            return Convert.ToInt32(choice);
        }

        public void AddCard(Card card)
        {
            CurrentHand.AddCard(card);
        }
    }
}
