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
    public partial class WelcomePage : UserControl
    {
        public event Action<Player> OnPlayClicked;

        public WelcomePage()
        {
            InitializeComponent();
        }

        private void PlayButton_Click(object sender, EventArgs e)
        {
            string playerName = NameBox.Text;
            if (!string.IsNullOrEmpty(playerName))
            {
                Player player = new Player(playerName,2500); 
                OnPlayClicked?.Invoke(player);
            }
            else
            {
                MessageBox.Show("Please enter your name!");
            }
        }
    }
}
