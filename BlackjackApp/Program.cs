using BlackjackApp;

Card card1 = new Card("3", Helper.Suit.Heart);
Card card2 = new Card("jack", Helper.Suit.Spade);
Card card3 = new Card("10", Helper.Suit.Diamond);

Hand PlayerHand=new Hand();

PlayerHand.AddCard(card1);

PlayerHand.AddCard(card2);

PlayerHand.ShowHand();

PlayerHand.AddCard(card3);

PlayerHand.ShowHand();

Console.WriteLine(PlayerHand.IsValidHand());
 