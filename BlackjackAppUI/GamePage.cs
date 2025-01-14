using BlackjackApp;
using Microsoft.VisualBasic.ApplicationServices;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;
using static System.Windows.Forms.VisualStyles.VisualStyleElement;

using Timer = System.Windows.Forms.Timer;

namespace BlackjackAppUI
{
    public partial class GamePage : UserControl
    {
        public event Action<Player> OnBackToBettingPage;
        private DeckOfCards deck;
        private Dealer dealer;
        private Player player;
        private int bet;
        public event Action OnPlayerEndTurn;
        private Timer dealerTurnTimer;
        public GamePage(Player player, int bet)
        {
            InitializeComponent();

            deck = new DeckOfCards();
            dealer = new Dealer();

            ImageList imageList = new ImageList
            {
                ImageSize = new System.Drawing.Size(70, 100) // Set size of images
            };

            foreach (Card item in deck.GetListOfCards())
            {
                imageList.Images.Add(item.ToString(), System.Drawing.Image.FromFile("playing_cards/" + item.ToString() + ".png"));

            }

            // Assign the ImageList to the ListView
            playerList.LargeImageList = imageList;
            DealerList.LargeImageList = imageList;

            playerList.View = View.LargeIcon;
            DealerList.View = View.LargeIcon;

            // Add items to the ListView


            this.player = player;
            this.bet = bet;

            player.AddToPocketMoney(-bet);

            player.ResetHand();
            dealer.ResetHand();

            dealerTurnTimer = new Timer();
            dealerTurnTimer.Interval = 1000; // Set the interval to 1 second (1000ms).
            dealerTurnTimer.Tick += DealerTurnTimer_Tick;

            deck = new DeckOfCards();
            deck.ShuffleDeck();

            HitButton.PerformClick();
            HitButton.PerformClick();

            string cardDetails = dealer.DealCard(deck, dealer).ToString();
            var card = new ListViewItem(cardDetails)
            {
                ImageKey = cardDetails
            };
            DealerList.Items.Add(card);
            DealerSumLabel.Text = "Sum = " + dealer.CurrentHand.GetSum().ToString();

            // Dealer Play

        }



        private void HitButton_Click(object sender, EventArgs e)
        {
            string cardDetails = dealer.DealCard(deck, player).ToString();
            var card = new ListViewItem(cardDetails)
            {
                ImageKey = cardDetails
            };
            playerList.Items.Add(card);
            PlayerSumLabel.Text = "Sum = " + player.CurrentHand.GetSum().ToString();

            if (player.CurrentHand.IsBust())
            {
                MessageBox.Show("You Lost!");
                OnBackToBettingPage?.Invoke(player);
            }
            if (player.CurrentHand.IsBlackJack())
            {
                MessageBox.Show("Blackjack!");
                StandButton.PerformClick();
            }
        }

        private void StandButton_Click(object sender, EventArgs e)
        {
            //OnPlayerEndTurn.Invoke();
            dealerTurnTimer.Start();
            StandButton.Enabled = false;
            HitButton.Enabled = false;
        }
        private void DealerTurnTimer_Tick(object sender, EventArgs e)
        {
            if (dealer.CurrentHand.IsBlackJack() || dealer.CurrentHand.IsBust())
            {
                dealerTurnTimer.Stop();
                DetermineWinner();
                return;
            }
            int choice = dealer.MakeChoice();
            if (choice == 1)
            {
                string cardDetails = dealer.DealCard(deck, dealer).ToString();
                var card = new ListViewItem(cardDetails)
                {
                    ImageKey = cardDetails
                };
                DealerList.Items.Add(card);
                DealerSumLabel.Text = "Sum = " + dealer.CurrentHand.GetSum().ToString();
            }
            else if (choice == 2)
            {
                dealerTurnTimer.Stop();
                DetermineWinner();
            }
        }
        private void DetermineWinner()
        {
            int DealerScore = dealer.CurrentHand.GetSum();
            int PlayerScore = player.CurrentHand.GetSum();

            if (DealerScore > 21 || PlayerScore > DealerScore)
            {
                MessageBox.Show("YOU WIN!");
                player.AddToPocketMoney(bet * 2);
            }
            else if (PlayerScore == DealerScore)
            {
                MessageBox.Show("Draw!");
                player.AddToPocketMoney(bet);
            }
            else
            {
                MessageBox.Show("You Lost!");
            }
            OnBackToBettingPage?.Invoke(player);
        }
    }
}
