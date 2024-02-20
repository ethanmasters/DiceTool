import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json

def read_monitoring_data(file_path='monitoring_data.json'):
    with open(file_path, 'r') as file:
        return json.load(file)

class DiceStatsDashboard:
    def __init__(self, file_path='monitoring_data.json'):
        self.file_path = file_path
        self.last_data = None
        self.window = tk.Tk()
        self.window.title("Dice Statistics Dashboard")
        
        self.labels = {
            'total_photos': tk.Label(self.window, text="Total Full Frame Photos: 0"),
            'total_dice': tk.Label(self.window, text="Total Cropped Dice Photos: 0")
        }
        self.labels['total_photos'].pack()
        self.labels['total_dice'].pack()
        
        # Placeholder for the bar graph
        self.figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.bar([], [])
        self.canvas = FigureCanvasTkAgg(self.figure, self.window)
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        self.update_gui()

    def update_gui(self):
        data = read_monitoring_data(self.file_path)
        
        # Update labels
        self.labels['total_photos'].config(text=f"Total Full Frame Photos: {data['total_full_frame_photos']}")
        self.labels['total_dice'].config(text=f"Total Cropped Dice Photos: {data['total_cropped_dice_photos']}")
        
        # Check if data has changed to update graph
        if data != self.last_data:
            self.last_data = data
            self.update_graph(data['dice_face_counts'])
        
        # Schedule the next update
        self.window.after(1000, self.update_gui)
    
    def update_graph(self, dice_counts):
        self.ax.clear()  # Clear the previous bar graph
        self.ax.bar(dice_counts.keys(), dice_counts.values())
        self.ax.set_title('Distribution of Dice Sides')
        self.canvas.draw()

def create_gui(file_path='monitoring_data.json'):
    dashboard = DiceStatsDashboard(file_path)
    dashboard.window.mainloop()

if __name__ == '__main__':
    create_gui()
