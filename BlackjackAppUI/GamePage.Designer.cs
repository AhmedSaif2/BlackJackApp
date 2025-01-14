namespace BlackjackAppUI
{
    partial class GamePage
    {
        /// <summary> 
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary> 
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Component Designer generated code

        /// <summary> 
        /// Required method for Designer support - do not modify 
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            playerList = new ListView();
            PlayerSumLabel = new Label();
            HitButton = new Button();
            StandButton = new Button();
            label1 = new Label();
            label2 = new Label();
            DealerList = new ListView();
            DealerSumLabel = new Label();
            SuspendLayout();
            // 
            // playerList
            // 
            playerList.BackColor = Color.SeaGreen;
            playerList.BorderStyle = BorderStyle.None;
            playerList.Location = new Point(65, 287);
            playerList.Name = "playerList";
            playerList.Size = new Size(642, 134);
            playerList.TabIndex = 1;
            playerList.UseCompatibleStateImageBehavior = false;
            playerList.View = View.List;
            // 
            // PlayerSumLabel
            // 
            PlayerSumLabel.AutoSize = true;
            PlayerSumLabel.Font = new Font("Segoe UI", 20F, FontStyle.Regular, GraphicsUnit.Point);
            PlayerSumLabel.ForeColor = Color.White;
            PlayerSumLabel.Location = new Point(490, 453);
            PlayerSumLabel.Name = "PlayerSumLabel";
            PlayerSumLabel.Size = new Size(116, 37);
            PlayerSumLabel.TabIndex = 2;
            PlayerSumLabel.Text = "Sum = 0";
            // 
            // HitButton
            // 
            HitButton.BackColor = Color.White;
            HitButton.Cursor = Cursors.Hand;
            HitButton.Font = new Font("Segoe UI", 15F, FontStyle.Regular, GraphicsUnit.Point);
            HitButton.Location = new Point(91, 453);
            HitButton.Name = "HitButton";
            HitButton.Size = new Size(118, 44);
            HitButton.TabIndex = 3;
            HitButton.Text = "Hit";
            HitButton.UseVisualStyleBackColor = false;
            HitButton.Click += HitButton_Click;
            // 
            // StandButton
            // 
            StandButton.BackColor = Color.White;
            StandButton.Font = new Font("Segoe UI", 15F, FontStyle.Regular, GraphicsUnit.Point);
            StandButton.Location = new Point(254, 453);
            StandButton.Name = "StandButton";
            StandButton.Size = new Size(118, 44);
            StandButton.TabIndex = 4;
            StandButton.Text = "Stand";
            StandButton.UseVisualStyleBackColor = false;
            StandButton.Click += StandButton_Click;
            // 
            // label1
            // 
            label1.AutoSize = true;
            label1.Font = new Font("Segoe UI", 20F, FontStyle.Regular, GraphicsUnit.Point);
            label1.ForeColor = Color.White;
            label1.Location = new Point(65, 16);
            label1.Name = "label1";
            label1.Size = new Size(168, 37);
            label1.TabIndex = 6;
            label1.Text = "Dealer Cards";
            // 
            // label2
            // 
            label2.AutoSize = true;
            label2.Font = new Font("Segoe UI", 20F, FontStyle.Regular, GraphicsUnit.Point);
            label2.ForeColor = Color.White;
            label2.Location = new Point(65, 233);
            label2.Name = "label2";
            label2.Size = new Size(144, 37);
            label2.TabIndex = 7;
            label2.Text = "Your Cards";
            // 
            // DealerList
            // 
            DealerList.BackColor = Color.SeaGreen;
            DealerList.BorderStyle = BorderStyle.None;
            DealerList.Location = new Point(65, 56);
            DealerList.Name = "DealerList";
            DealerList.Size = new Size(642, 134);
            DealerList.TabIndex = 8;
            DealerList.UseCompatibleStateImageBehavior = false;
            DealerList.View = View.List;
            // 
            // DealerSumLabel
            // 
            DealerSumLabel.AutoSize = true;
            DealerSumLabel.Font = new Font("Segoe UI", 20F, FontStyle.Regular, GraphicsUnit.Point);
            DealerSumLabel.ForeColor = Color.White;
            DealerSumLabel.Location = new Point(490, 16);
            DealerSumLabel.Name = "DealerSumLabel";
            DealerSumLabel.Size = new Size(116, 37);
            DealerSumLabel.TabIndex = 9;
            DealerSumLabel.Text = "Sum = 0";
            // 
            // GamePage
            // 
            AutoScaleDimensions = new SizeF(7F, 15F);
            AutoScaleMode = AutoScaleMode.Font;
            BackColor = Color.SeaGreen;
            Controls.Add(DealerSumLabel);
            Controls.Add(DealerList);
            Controls.Add(label2);
            Controls.Add(label1);
            Controls.Add(StandButton);
            Controls.Add(HitButton);
            Controls.Add(PlayerSumLabel);
            Controls.Add(playerList);
            Name = "GamePage";
            Size = new Size(760, 522);
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion
        private ListView playerList;
        private Label PlayerSumLabel;
        private Button HitButton;
        private Button StandButton;
        private Label label1;
        private Label label2;
        private ListView DealerList;
        private Label DealerSumLabel;
    }
}
