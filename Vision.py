import tkinter as tk
import pygetwindow as gw
import threading
import time

def check_active_window():
    while True:
        active_window = gw.getActiveWindow()  # Отримуємо активне вікно
        if active_window:
            window_title = active_window.title
            if "Google Chrome" in window_title or "Chrome" in window_title:
                update_gui(f"Ви серфите Інтернет на Google Chrome: {window_title}")
            else:
                update_gui(f"Активне вікно: {window_title}")
        else:
            update_gui("Не вдалося отримати активне вікно.")
        time.sleep(2)  # Затримка перед наступним перевіренням

def update_gui(text):
    output_label.config(text=text)

def start_monitoring():
    monitoring_thread = threading.Thread(target=check_active_window, daemon=True)
    monitoring_thread.start()

# Створення GUI
root = tk.Tk()
root.title("Active Window Monitor")

output_label = tk.Label(root, text="Запуск аналізу...", font=("Arial", 14))
output_label.pack(pady=20)

start_monitoring()  # Запускаємо моніторинг у фоновому режимі

root.mainloop()
