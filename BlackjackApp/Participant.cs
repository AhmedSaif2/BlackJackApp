using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace BlackjackApp
{
    public abstract class Participant
    {
        protected string? Name;
        public Hand CurrentHand { get; set; }
        public Participant()
        {
            CurrentHand = new Hand();
        }
        public abstract int MakeChoice();
        public void SeeHand()
        {
            CurrentHand.ShowHand();
        }
        public void AddCard(Card card)
        {
            CurrentHand.AddCard(card);
        }
        public void ResetHand()
        {
            CurrentHand = new Hand();
        }
    }
}
