using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace BlackjackApp
{
    public class Player
    {
        public string?Name { get; set; }
        public Hand CurrentHand { get; set; }
        private int PocketMoney;
        //public int PocketMoney { get; set; }
        public Player() { 
            CurrentHand = new Hand();
        }
        public Player(string name,int pocketMoney) { 
            Name= name;
            PocketMoney= pocketMoney;
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
        public bool PlaceBet(int bet)
        {
            if (bet <= PocketMoney)
            {
                PocketMoney -= bet;
                return true;
            }
            else
            {
                Console.WriteLine("Not Enough Pocket Money!");
                return false;
            }
        }
        public int GetPocketMoney()
        {
            return PocketMoney;
        }

        public void AddToPocketMoney(int bet)
        {
            PocketMoney += bet;
        }

        public void ResetHand()
        {
            CurrentHand= new Hand();
        }
    }
}
