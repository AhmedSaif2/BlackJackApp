using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace BlackjackApp
{
    public class Player : Participant
    {
        private int PocketMoney;
        //public int PocketMoney { get; set; }
        
        public Player(string name,int pocketMoney) { 
            Name= name;
            PocketMoney= pocketMoney;
            CurrentHand=new Hand();
        }
        
        public override int MakeChoice()
        {
            // 1 for Hit
            // 2 for Stand
            Console.WriteLine("Type 1 to Hit Or 2 To Stand");
            string choice = Console.ReadLine();
            return Convert.ToInt32(choice);
        }

        public bool PlaceBet(int bet)
        {
            if (bet <= PocketMoney)
            {
                PocketMoney -= bet;
                return true;
            }
            Console.WriteLine("Not Enough Pocket Money!");
            return false;
        }
        public int GetPocketMoney()
        {
            return PocketMoney;
        }

        public void AddToPocketMoney(int bet)
        {
            PocketMoney += bet;
        }

        
    }
}
