using BlackjackApp;


Console.WriteLine("-------------------------- New Game --------------------------");
Console.WriteLine("Please Enter Your Name: ");

string PlayerName = Console.ReadLine();
Player player = new Player(PlayerName, 2500);

Dealer dealer = new Dealer(); 


while (true)
{
    BlackjackGame Game = new BlackjackGame(dealer,player);
    Game.SetBet(50);
    if (player.GetPocketMoney() == 0) return;
}
