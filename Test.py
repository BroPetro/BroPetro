import speech_recognition as sr
from gtts import gTTS
import os
import pygame
import webbrowser
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
import random
import datetime
import time
import pyautogui  # Для реалізації кліків

class VoiceAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Assistant")
        self.root.configure(bg="#1e1e1e")

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
        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.pack(expand=1, fill='both')

        self.tab_assistant = ttk.Frame(self.tab_control)
        self.tab_terminal = ttk.Frame(self.tab_control)
        self.tab_settings = ttk.Frame(self.tab_control)

        self.tab_control.add(self.tab_assistant, text='Асистент')
        self.tab_control.add(self.tab_terminal, text='Термінал')
        self.tab_control.add(self.tab_settings, text='Налаштування')

        # Асистент
        self.output_text = scrolledtext.ScrolledText(self.tab_assistant, wrap=tk.WORD, width=50, height=20, font=("Arial", 12), bg="#000000", fg="#00BFFF")
        self.output_text.pack(padx=10, pady=10)

        self.listen_button = tk.Button(self.tab_assistant, text="Включити асистента", command=self.start_listening_thread, font=("Arial", 12), bg="#00BFFF", fg="#1e1e1e")
        self.listen_button.pack(pady=10)

        self.voice_toggle_button = tk.Button(self.tab_assistant, text="Виключити голос", command=self.toggle_voice, font=("Arial", 12), bg="#00BFFF", fg="#1e1e1e")
        self.voice_toggle_button.pack(pady=10)

        self.quit_button = tk.Button(self.tab_assistant, text="Вийти", command=self.root.quit, font=("Arial", 12), bg="#00BFFF", fg="#1e1e1e")
        self.quit_button.pack(pady=10)

        # Термінал
        self.terminal_text = scrolledtext.ScrolledText(self.tab_terminal, wrap=tk.WORD, width=50, height=20, font=("Arial", 12), bg="#000000", fg="#00BFFF")
        self.terminal_text.pack(padx=10, pady=10)

        self.command_entry = tk.Entry(self.tab_terminal, font=("Arial", 12), width=50)
        self.command_entry.pack(padx=10, pady=5)

        self.command_button = tk.Button(self.tab_terminal, text="Виконати", command=self.execute_command, font=("Arial", 12), bg="#00BFFF", fg="#1e1e1e")
        self.command_button.pack(pady=5)

        # Налаштування
        self.additional_commands_label = tk.Label(self.tab_settings, text="Додати команду:", font=("Arial", 12), bg="#1e1e1e", fg="#00BFFF")
        self.additional_commands_label.pack(pady=10)

        self.command_entry_custom = tk.Entry(self.tab_settings, font=("Arial", 12), width=50)
        self.command_entry_custom.pack(pady=10)

        self.save_commands_button = tk.Button(self.tab_settings, text="Зберегти команду", command=self.save_custom_command, font=("Arial", 12), bg="#00BFFF", fg="#1e1e1e")
        self.save_commands_button.pack(pady=10)

        self.face_button = tk.Button(self.tab_settings, text="Лице", command=self.open_cute_face_window, font=("Arial", 12), bg="#00BFFF", fg="#1e1e1e")
        self.face_button.pack(pady=10)

        self.volume_label = tk.Label(self.tab_settings, text="Гучність:", font=("Arial", 12), bg="#1e1e1e", fg="#00BFFF")
        self.volume_label.pack(pady=10)

        self.volume_scale = tk.Scale(self.tab_settings, from_=0, to=100, orient=tk.HORIZONTAL, command=self.change_volume, length=200)
        self.volume_scale.set(100)
        self.volume_scale.pack(pady=10)

        self.speech_speed_label = tk.Label(self.tab_settings, text="Швидкість мовлення:", font=("Arial", 12), bg="#1e1e1e", fg="#00BFFF")
        self.speech_speed_label.pack(pady=10)

        self.speech_speed_scale = tk.Scale(self.tab_settings, from_=50, to=150, orient=tk.HORIZONTAL, command=self.change_speech_speed, length=200)
        self.speech_speed_scale.set(100)
        self.speech_speed_scale.pack(pady=10)

        self.output_device_label = tk.Label(self.tab_settings, text="Пристрій виводу:", font=("Arial", 12), bg="#1e1e1e", fg="#00BFFF")
        self.output_device_label.pack(pady=10)

        self.output_device_var = tk.StringVar(value="default")
        self.output_device_menu = ttk.Combobox(self.tab_settings, textvariable=self.output_device_var, values=["default", "headphones", "speakers"])
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

            pygame.mixer.quit()
            os.remove(filename)
        except Exception as e:
            self.update_text(f"Error: {e}")

    def listen(self):
        self.update_text("Слухаю...")
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
            try:
                command = recognizer.recognize_google(audio, language="uk-UA")
                self.update_text(f"Ви сказали: {command}")
                return command
            except sr.UnknownValueError:
                self.update_text("Не зрозуміло, що ви сказали. Спробуйте ще раз.")
                return ""
            except sr.RequestError as e:
                self.update_text(f"Проблема з сервісом розпізнавання мови: {e}")
                return ""

    def generate_response(self, question):
        if question in self.custom_commands:
            response = self.custom_commands[question]
            if "<--" in response:
                parts = response.split("<--")
                if len(parts) == 2 and random.random() < 0.5:
                    return parts[1].strip()
                else:
                    return parts[0].strip()
            return response.strip()

        responses = {
            "привіт": ["Привіт! Як справи?", "Привіт, як я можу вам допомогти?"],
            "як тебе звати": ["Мене звати Асистент.", "Ви можете звати мене Асистентом."],
            "що ти вмієш": ["Я можу відповідати на ваші запитання та допомагати з інформацією.", "Мої основні функції - це відповіді на запитання та виконання команд."],
            "до побачення": ["До побачення! Гарного дня!", "Бувайте, до зустрічі!"],
            "відкрий google": ["Відкриваю Google...", "Дозвольте мені відкрити Google."],
            "відкрий roblox": ["Відкриваю Roblox...", "Розпочинаю гру Roblox."],
            "яка година": [f"Зараз {datetime.datetime.now().strftime('%H:%M:%S')}"],
            "автоклікер": ["Розпочинаю періодичні кліки кожні 2 секунди.", "Зараз почну клікати."],
            "стоп автоклікер": ["Зупиняю кліки.", "Кліки зупинено."]
        }

        for key, response in responses.items():
            if key in question:
                if key == "автоклікер":
                    threading.Thread(target=self.start_clicking, args=(2,)).start()
                elif key == "стоп автоклікер":
                    self.stop_clicking()
                if isinstance(response, list):
                    return random.choice(response)
                else:
                    return response

        return "Вибачте, я не розумію вашого запиту."

    def open_application(self, app_name):
        applications = {
            "файловий провідник": "explorer",
            "нотатник": "notepad",
            "калькулятор": "calc"
        }
        if app_name in applications:
            os.system(applications[app_name])
            return f"Відкриваю {app_name}"
        else:
            return f"Не можу знайти програму {app_name}"

    def start_clicking(self, interval):
        self.clicking_active = True
        while self.clicking_active:
            pyautogui.click()
            time.sleep(interval)

    def stop_clicking(self):
        self.clicking_active = False

    def main(self):
        while self.assistant_active:
            command = self.listen().lower()
            if not command:
                continue
            if 'стоп' in command:
                response = "До побачення!"
                self.update_text(f"Assistant: {response}")
                self.speak(response)
                self.assistant_active = False
                break
            if 'відкрий' in command:
                app_name = command.replace('відкрий', '').strip()
                response = self.open_application(app_name)
                self.update_text(f"Assistant: {response}")
                self.speak(response)
                continue
            if 'загугли' in command:
                search_query = command.replace('загугли', '').strip()
                response = f"Зараз знайду інформацію про {search_query}."
                self.update_text(f"Assistant: {response}")
                self.speak(response)
                webbrowser.open(f"https://www.google.com/search?q={search_query}")
                continue
            response = self.generate_response(command)
            self.update_text(f"Assistant: {response}")
            self.speak(response)

    def execute_command(self):
        command = self.command_entry.get().lower()
        self.update_terminal(f"Ви ввели команду: {command}")
        response = self.generate_response(command)
        self.update_terminal(f"Assistant: {response}")
        self.command_entry.delete(0, tk.END)
        self.speak(response)

    def open_cute_face_window(self):
        face_window = tk.Toplevel(self.root)
        face_window.title("Миле обличчя")
        face_window.geometry("300x300")
        face_window.configure(bg="#87CEEB")

        canvas = tk.Canvas(face_window, width=300, height=300, bg="#87CEEB", highlightthickness=0)
        canvas.pack()

        face_color = "#ADD8E6"
        eye_color = "white"
        pupil_color = "black"

        face = canvas.create_rectangle(100, 100, 200, 200, outline="black", fill=face_color)
        left_eye = canvas.create_rectangle(120, 130, 150, 160, outline="black", fill=eye_color)
        right_eye = canvas.create_rectangle(170, 130, 200, 160, outline="black", fill=eye_color)
        left_pupil = canvas.create_oval(135, 145, 145, 155, fill=pupil_color)
        right_pupil = canvas.create_oval(185, 145, 195, 155, fill=pupil_color)

        def animate_face():
            nonlocal face_color, eye_color, pupil_color
            while True:
                if random.random() < 0.1:
                    canvas.itemconfig(left_eye, fill=face_color)
                    canvas.itemconfig(right_eye, fill=face_color)
                    canvas.itemconfig(left_pupil, state=tk.NORMAL)
                    canvas.itemconfig(right_pupil, state=tk.NORMAL)
                else:
                    canvas.itemconfig(left_eye, fill=eye_color)
                    canvas.itemconfig(right_eye, fill=eye_color)
                    canvas.itemconfig(left_pupil, state=tk.HIDDEN)
                    canvas.itemconfig(right_pupil, state=tk.HIDDEN)
                time.sleep(0.5)

        def blink():
            nonlocal eye_color
            while True:
                canvas.itemconfig(left_eye, fill=face_color)
                canvas.itemconfig(right_eye, fill=face_color)
                time.sleep(0.3)
                canvas.itemconfig(left_eye, fill=eye_color)
                canvas.itemconfig(right_eye, fill=eye_color)
                time.sleep(3)

        def react_to_mouse(event):
            canvas.itemconfig(left_pupil, state=tk.NORMAL)
            canvas.itemconfig(right_pupil, state=tk.NORMAL)

        canvas.bind("<Motion>", react_to_mouse)

        threading.Thread(target=animate_face, daemon=True).start()
        threading.Thread(target=blink, daemon=True).start()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceAssistantApp(root)
    app.run()
