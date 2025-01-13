namespace BlackjackAppUI
{
    partial class BettingPage
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
            button3 = new Button();
            button2 = new Button();
            button1 = new Button();
            label1 = new Label();
            WelcomeLabel = new Label();
            MoneyLabel = new Label();
            SuspendLayout();
            // 
            // button3
            // 
            button3.Font = new Font("Segoe UI", 15F, FontStyle.Regular, GraphicsUnit.Point);
            button3.Location = new Point(504, 378);
            button3.Name = "button3";
            button3.Size = new Size(82, 42);
            button3.TabIndex = 9;
            button3.Text = "200$";
            button3.UseVisualStyleBackColor = true;
            button3.Click += button3_Click;
            // 
            // button2
            // 
            button2.Font = new Font("Segoe UI", 15F, FontStyle.Regular, GraphicsUnit.Point);
            button2.Location = new Point(312, 378);
            button2.Name = "button2";
            button2.Size = new Size(82, 42);
            button2.TabIndex = 8;
            button2.Text = "50$";
            button2.UseVisualStyleBackColor = true;
            button2.Click += button2_Click;
            // 
            // button1
            // 
            button1.Font = new Font("Segoe UI", 15F, FontStyle.Regular, GraphicsUnit.Point);
            button1.Location = new Point(115, 378);
            button1.Name = "button1";
            button1.Size = new Size(82, 42);
            button1.TabIndex = 7;
            button1.Text = "10$";
            button1.UseVisualStyleBackColor = true;
            button1.Click += button1_Click;
            // 
            // label1
            // 
            label1.AutoSize = true;
            label1.Font = new Font("Segoe UI", 20F, FontStyle.Regular, GraphicsUnit.Point);
            label1.Location = new Point(260, 256);
            label1.Name = "label1";
            label1.Size = new Size(185, 37);
            label1.TabIndex = 6;
            label1.Text = "Place your bet";
            // 
            // WelcomeLabel
            // 
            WelcomeLabel.AutoSize = true;
            WelcomeLabel.Font = new Font("Segoe UI", 20F, FontStyle.Regular, GraphicsUnit.Point);
            WelcomeLabel.Location = new Point(161, 94);
            WelcomeLabel.Name = "WelcomeLabel";
            WelcomeLabel.Size = new Size(90, 37);
            WelcomeLabel.TabIndex = 5;
            WelcomeLabel.Text = "label1";
            // 
            // MoneyLabel
            // 
            MoneyLabel.AutoSize = true;
            MoneyLabel.Font = new Font("Segoe UI", 20F, FontStyle.Regular, GraphicsUnit.Point);
            MoneyLabel.Location = new Point(161, 176);
            MoneyLabel.Name = "MoneyLabel";
            MoneyLabel.Size = new Size(90, 37);
            MoneyLabel.TabIndex = 10;
            MoneyLabel.Text = "label2";
            // 
            // BettingPage
            // 
            AutoScaleDimensions = new SizeF(7F, 15F);
            AutoScaleMode = AutoScaleMode.Font;
            Controls.Add(MoneyLabel);
            Controls.Add(button3);
            Controls.Add(button2);
            Controls.Add(button1);
            Controls.Add(label1);
            Controls.Add(WelcomeLabel);
            Name = "BettingPage";
            Size = new Size(747, 532);
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private Button button3;
        private Button button2;
        private Button button1;
        private Label label1;
        private Label WelcomeLabel;
        private Label MoneyLabel;
    }
}
