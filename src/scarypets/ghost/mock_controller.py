import tkinter as tk


def launch_controller(on_button1, on_button2, on_button3, on_button4, on_button5):
  root = tk.Tk()
  root.title("Graveyard Pet Controller")
  root.geometry("220x320")

  tk.Label(root, text="Mock Controller", font=("Arial", 12, "bold")).pack(pady=10)

  tk.Button(root, text="Power", bg='#ff9696', width=20, height=2, command=on_button1).pack(pady=5)
  tk.Button(root, text="Scare!", width=20, height=2, command=on_button2).pack(pady=5)
  tk.Button(root, text="Add Ghost", width=20, height=2, command=on_button3).pack(pady=5)
  tk.Button(root, text="Remove Ghost", width=20, height=2, command=on_button4).pack(pady=5)
  tk.Button(root, text="Emote", width=20, height=2, command=on_button5).pack(pady=5)

  root.mainloop()