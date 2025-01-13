using BlackjackApp;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace BlackjackAppUI
{
    public partial class BettingPage : UserControl
    {
        public event Action<int> OnBetPlaced;

        public BettingPage(Player player)
        {
            InitializeComponent();
            WelcomeLabel.Text = "Welcome " + player.GetName();
            MoneyLabel.Text = "Pocket Money = " + player.GetPocketMoney();
        }

        private void button1_Click(object sender, EventArgs e)
        {
            OnBetPlaced?.Invoke(10);
        }

        private void button2_Click(object sender, EventArgs e)
        {
            OnBetPlaced?.Invoke(50);
        }

        private void button3_Click(object sender, EventArgs e)
        {
            OnBetPlaced?.Invoke(200);
        }
    }
}
