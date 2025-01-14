using BlackjackApp;
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Numerics;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace BlackjackAppUI
{
    public partial class MainForm : Form
    {
        private BettingPage bettingPage;

        public MainForm()
        {
            InitializeComponent();

            LoadWelcomePage();
        }
        private void LoadWelcomePage()
        {
            MainPanel.Controls.Clear();
            WelcomePage welcomePage = new WelcomePage();
            welcomePage.OnPlayClicked += player => LoadBettingPage(player);
            MainPanel.Controls.Add(welcomePage);
            welcomePage.Dock = DockStyle.Fill;
        }
        private void LoadBettingPage(Player player)
        {
            MainPanel.Controls.Clear();
            BettingPage bettingPage = new BettingPage(player);
            bettingPage.OnBetPlaced += betAmount => StartGame(player, betAmount);
            MainPanel.Controls.Add(bettingPage);
            bettingPage.Dock = DockStyle.Fill;
        }
        private void StartGame(Player player, int betAmount)
        {
            MainPanel.Controls.Clear();
            GamePage gamePage = new GamePage(player, betAmount);
            gamePage.OnBackToBettingPage += (player) => LoadBettingPage(player);
            MainPanel.Controls.Add(gamePage);
            gamePage.Dock = DockStyle.Fill;
        }
    }
}
