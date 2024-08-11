import speech_recognition as sr
from gtts import gTTS
import os
import pygame
import webbrowser
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
import pyautogui
import time

class VoiceAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Assistant")
        self.root.geometry("800x600")
        self.root.configure(bg="#000000")

        self.voice_enabled = True
        self.voice_gender = 'female'
        self.assistant_active = False
        self.volume = 1.0
        self.speech_speed = 1.0
        self.output_device = "default"
        self.clicking_active = False
        self.custom_commands = {}

        self.load_custom_commands()
        self.create_widgets()

    def create_widgets(self):
        style = ttk.Style()
        style.configure('TFrame', background='#FFD700')
        style.configure('TNotebook.Tab', background='#FFA500', foreground='#000000', padding=[10, 5])
        style.map('TNotebook.Tab', background=[('selected', '#FF6347')])

        self.tab_control = ttk.Notebook(self.root, style='TNotebook')
        self.tab_control.pack(expand=1, fill='both')

        self.tab_assistant = ttk.Frame(self.tab_control, style='TFrame')
        self.tab_terminal = ttk.Frame(self.tab_control, style='TFrame')
        self.tab_settings = ttk.Frame(self.tab_control, style='TFrame')

        self.tab_control.add(self.tab_assistant, text='Асистент')
        self.tab_control.add(self.tab_terminal, text='Термінал')
        self.tab_control.add(self.tab_settings, text='Налаштування')

        # Асистент
        self.output_text = scrolledtext.ScrolledText(self.tab_assistant, wrap=tk.WORD, width=80, height=20, font=("Arial", 12), bg="#000000", fg="#FFD700")
        self.output_text.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        self.listen_button = tk.Button(self.tab_assistant, text="Включити асистента", command=self.start_listening_thread, font=("Arial", 14), bg="#FF6347", fg="#000000")
        self.listen_button.pack(pady=10, fill=tk.X)

        self.voice_toggle_button = tk.Button(self.tab_assistant, text="Виключити голос", command=self.toggle_voice, font=("Arial", 14), bg="#FF6347", fg="#000000")
        self.voice_toggle_button.pack(pady=10, fill=tk.X)

        self.quit_button = tk.Button(self.tab_assistant, text="Вийти", command=self.root.quit, font=("Arial", 14), bg="#FF6347", fg="#000000")
        self.quit_button.pack(pady=10, fill=tk.X)

        # Термінал
        self.terminal_text = scrolledtext.ScrolledText(self.tab_terminal, wrap=tk.WORD, width=80, height=20, font=("Arial", 12), bg="#000000", fg="#FFD700")
        self.terminal_text.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        self.command_entry = tk.Entry(self.tab_terminal, font=("Arial", 14), width=70)
        self.command_entry.pack(padx=20, pady=10)

        self.command_button = tk.Button(self.tab_terminal, text="Виконати", command=self.execute_command, font=("Arial", 14), bg="#FF6347", fg="#000000")
        self.command_button.pack(pady=10, fill=tk.X)

        # Налаштування
        self.additional_commands_label = tk.Label(self.tab_settings, text="Додати команду:", font=("Arial", 14), bg="#FFD700", fg="#000000")
        self.additional_commands_label.pack(pady=20)

        self.command_entry_custom = tk.Entry(self.tab_settings, font=("Arial", 14), width=70)
        self.command_entry_custom.pack(pady=10)

        self.save_commands_button = tk.Button(self.tab_settings, text="Зберегти команду", command=self.save_custom_command, font=("Arial", 14), bg="#FF6347", fg="#000000")
        self.save_commands_button.pack(pady=10)

        self.face_button = tk.Button(self.tab_settings, text="Лице", command=self.open_cute_face_window, font=("Arial", 14), bg="#FF6347", fg="#000000")
        self.face_button.pack(pady=10)

        self.volume_label = tk.Label(self.tab_settings, text="Гучність:", font=("Arial", 14), bg="#FFD700", fg="#000000")
        self.volume_label.pack(pady=20)

        self.volume_scale = tk.Scale(self.tab_settings, from_=0, to=100, orient=tk.HORIZONTAL, command=self.change_volume, length=400, bg="#FFD700", fg="#000000", troughcolor="#FFA500")
        self.volume_scale.set(100)
        self.volume_scale.pack(pady=10)

        self.speech_speed_label = tk.Label(self.tab_settings, text="Швидкість мовлення:", font=("Arial", 14), bg="#FFD700", fg="#000000")
        self.speech_speed_label.pack(pady=20)

        self.speech_speed_scale = tk.Scale(self.tab_settings, from_=50, to=150, orient=tk.HORIZONTAL, command=self.change_speech_speed, length=400, bg="#FFD700", fg="#000000", troughcolor="#FFA500")
        self.speech_speed_scale.set(100)
        self.speech_speed_scale.pack(pady=10)

        self.output_device_label = tk.Label(self.tab_settings, text="Пристрій виводу:", font=("Arial", 14), bg="#FFD700", fg="#000000")
        self.output_device_label.pack(pady=20)

        self.output_device_var = tk.StringVar(value="default")
        self.output_device_menu = ttk.Combobox(self.tab_settings, textvariable=self.output_device_var, values=["default", "headphones", "speakers"], font=("Arial", 14))
        self.output_device_menu.pack(pady=10)
        self.output_device_menu.bind("<<ComboboxSelected>>", self.change_output_device)

    def save_custom_command(self):
        command_text = self.command_entry_custom.get()
        if "--" not in command_text:
            messagebox.showerror("Помилка", "Команда повинна містити '--' для розділення команди і відповіді.")
            return

        command, response = command_text.split("--", 1)
        command = command.strip()
        response = response.strip()

        self.custom_commands[command] = response
        self.update_text(f"Додано нову команду: {command}")

        # Очищення поля введення
        self.command_entry_custom.delete(0, tk.END)
        self.save_custom_commands()

    def load_custom_commands(self):
        try:
            with open("custom_commands.txt", "r", encoding="utf-8") as file:
                for line in file:
                    if "--" in line:
                        command, response = line.strip().split("--", 1)
                        self.custom_commands[command.strip()] = response.strip()
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error loading custom commands: {e}")

    def save_custom_commands(self):
        try:
            with open("custom_commands.txt", "w", encoding="utf-8") as file:
                for command, response in self.custom_commands.items():
                    file.write(f"{command} -- {response}\n")
        except Exception as e:
            print(f"Error saving custom commands: {e}")

    def start_listening_thread(self):
        if not self.assistant_active:
            self.assistant_active = True
            self.listening_thread = threading.Thread(target=self.main)
            self.listening_thread.start()

    def toggle_voice(self):
        self.voice_enabled = not self.voice_enabled
        status = "виключений" if not self.voice_enabled else "включений"
        self.update_text(f"Голос асистента {status}.")
        self.voice_toggle_button.config(text="Включити голос" if not self.voice_enabled else "Виключити голос")

    def change_volume(self, value):
        self.volume = int(value) / 100

    def change_speech_speed(self, value):
        self.speech_speed = int(value) / 100

    def change_output_device(self, event):
        self.output_device = self.output_device_var.get()

    def update_text(self, text):
        self.output_text.insert(tk.END, text + '\n')
        self.output_text.see(tk.END)

    def update_terminal(self, text):
        self.terminal_text.insert(tk.END, text + '\n')
        self.terminal_text.see(tk.END)

    def speak(self, text):
        if not self.voice_enabled:
            return
        try:
            tts = gTTS(text=text, lang='uk', slow=(self.speech_speed < 1.0))
            filename = "voice.mp3"
            tts.save(filename)

            pygame.mixer.init()
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                continue

            pygame.mixer.music.stop()
            os.remove(filename)

        except Exception as e:
            print(f"Error in speech synthesis: {e}")

    def listen(self):
        self.update_text("Слухаю...")
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
            try:
                command = recognizer.recognize_google(audio, language='uk-UA')
                self.update_text(f"Ви сказали: {command}")

                response = self.custom_commands.get(command, None)
                if response:
                    self.speak(response)
                elif "відкрий" in command.lower():
                    self.open_website(command)
                elif "натисни" in command.lower():
                    self.click_on_command(command)
                else:
                    self.speak("Я не розумію команду.")

            except sr.UnknownValueError:
                self.speak("Не вдалося розпізнати команду.")
            except sr.RequestError as e:
                self.speak(f"Помилка сервісу розпізнавання: {e}")

    def open_website(self, command):
        urls = {
            "ютуб": "https://www.youtube.com",
            "гімн": "https://www.youtube.com/watch?v=3k5D-6p3BWI"
        }
        for keyword, url in urls.items():
            if keyword in command.lower():
                webbrowser.open(url)
                self.speak(f"Відкриваю {keyword}.")
                return
        self.speak("Не можу знайти відповідний веб-сайт.")

    def click_on_command(self, command):
        if "натисни" in command.lower():
            self.clicking_active = True
            self.update_text("Натискання активоване.")
        elif "зупини" in command.lower():
            self.clicking_active = False
            self.update_text("Натискання зупинене.")
        while self.clicking_active:
            pyautogui.click()
            time.sleep(0.5)

    def main(self):
        while self.assistant_active:
            self.listen()

    def execute_command(self):
        command_text = self.command_entry.get()
        self.update_terminal(f"Виконання команди: {command_text}")
        self.command_entry.delete(0, tk.END)

    def open_cute_face_window(self):
        cute_face_window = tk.Toplevel(self.root)
        cute_face_window.title("Cute Face")
        cute_face_window.geometry("300x300")
        cute_face_window.configure(bg="#FFD700")

        face_label = tk.Label(cute_face_window, text="😊", font=("Arial", 100), bg="#FFD700")
        face_label.pack(pady=50)

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceAssistantApp(root)
    root.mainloop()
