namespace BlackjackAppUI
{
    partial class WelcomePage
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
            PlayButton = new Button();
            NameBox = new TextBox();
            label2 = new Label();
            label1 = new Label();
            SuspendLayout();
            // 
            // PlayButton
            // 
            PlayButton.Location = new Point(281, 346);
            PlayButton.Name = "PlayButton";
            PlayButton.Size = new Size(147, 58);
            PlayButton.TabIndex = 7;
            PlayButton.Text = "Play";
            PlayButton.UseVisualStyleBackColor = true;
            PlayButton.Click += PlayButton_Click;
            // 
            // NameBox
            // 
            NameBox.Font = new Font("Segoe UI", 20F, FontStyle.Regular, GraphicsUnit.Point);
            NameBox.Location = new Point(309, 224);
            NameBox.Name = "NameBox";
            NameBox.Size = new Size(355, 43);
            NameBox.TabIndex = 6;
            // 
            // label2
            // 
            label2.AutoSize = true;
            label2.Font = new Font("Segoe UI", 20F, FontStyle.Regular, GraphicsUnit.Point);
            label2.Location = new Point(62, 224);
            label2.Name = "label2";
            label2.Size = new Size(216, 37);
            label2.TabIndex = 5;
            label2.Text = "Enter Your Name";
            // 
            // label1
            // 
            label1.AutoSize = true;
            label1.Font = new Font("Segoe UI", 36F, FontStyle.Regular, GraphicsUnit.Point);
            label1.Location = new Point(250, 116);
            label1.Name = "label1";
            label1.Size = new Size(220, 65);
            label1.TabIndex = 4;
            label1.Text = "Blackjack";
            // 
            // WelcomePage
            // 
            AutoScaleDimensions = new SizeF(7F, 15F);
            AutoScaleMode = AutoScaleMode.Font;
            Controls.Add(PlayButton);
            Controls.Add(NameBox);
            Controls.Add(label2);
            Controls.Add(label1);
            Name = "WelcomePage";
            Size = new Size(747, 532);
            ResumeLayout(false);
            PerformLayout();
        }

        #endregion

        private Button PlayButton;
        private TextBox NameBox;
        private Label label2;
        private Label label1;
    }
}
