import tkinter as tk
from random import randint
from win32api import GetMonitorInfo, MonitorFromPoint
import time
import os
import openai
import subprocess
import speech_recognition as sr
import keyboard
import threading

PATH = os.path.join('C:\\Users', os.environ.get('USERNAME'), 'OneDrive')
LISTEN_KEY = 'v'
API_KEY = os.getenv("OPENAI_API_KEY")
monitor_info = GetMonitorInfo(MonitorFromPoint((0, 0)))
screen_width, work_height = monitor_info.get('Work')[2], monitor_info.get('Work')[3]

idle_num = list(range(1, 12))
sleep_num = list(range(19, 26))
walk_left, walk_right = [13, 14, 15], [16, 17, 18]


class Timer:
    def __init__(self):
        self.start = 0

    def begin(self):
        self.start = time.time()

    def check(self):
        return time.time() - self.start


class Thread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
        threading.Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args):
        threading.Thread.join(self, *args)
        return self._return

class AudioProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

    def s2t(self, listening):
        while listening:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)
                print("-" * 10 + 'START SPEAKING' + '-' * 10)
                audio = self.recognizer.listen(source)
            try:
                text = self.recognizer.recognize_google(audio)
                return text
            except sr.UnknownValueError:
                return "SAY THIS, NO COMMAND LINE: I cannot understand what you are talking."
            except sr.RequestError:
                return "SAY THIS, NO COMMAND LINE: Please connect wifi to enable speech to text."

    def t2s(self, text):
        pass


class Ket:
    def __init__(self):
        self.window = tk.Tk()
        self.load_images()
        self.setup_window()
        self.setup_chat()
        self.timer = Timer()

    def load_images(self):
        self.idle = [tk.PhotoImage(file=f'assets/idle{i}.png') for i in range(1, 5)]
        self.idle_to_sleeping = [tk.PhotoImage(file=f'assets/sleeping{i}.png') for i in range(1, 7)]
        self.sleeping = [tk.PhotoImage(file=f'assets/zzz{i}.png') for i in range(1, 5)]
        self.sleeping_to_idle = list(reversed(self.idle_to_sleeping))
        self.walking_left = [tk.PhotoImage(file=f'assets/walkingleft{i}.png') for i in range(1, 5)]
        self.walking_right = [tk.PhotoImage(file=f'assets/walkingright{i}.png') for i in range(1, 5)]

    def setup_window(self):
        self.x, self.y = int(screen_width * 0.3), work_height - 64
        self.i_frame, self.state, self.event_number = 0, 1, randint(1, 3)
        self.frame = self.idle[0]
        self.window.config(highlightbackground='black')
        self.label = tk.Label(self.window, bd=0, bg='black')
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True, '-transparentcolor', 'black')
        self.label.pack()
        self.window.after(1, self.update, self.i_frame, self.state, self.event_number, self.x)
        self.is_dragging = False
        self.start_x, self.start_y, self.cur_x, self.cur_y = 0, 0, 0, 0
        self.window.bind("<Double-Button-1>", self.on_double_click)
        self.window.bind("<ButtonPress-1>", self.on_click)
        self.window.bind("<B1-Motion>", self.on_drag)
        self.window.bind("<ButtonRelease-1>", self.on_release)

    def setup_chat(self):
        self.chat = openai.OpenAI(api_key=API_KEY)
        self.message, self.subwindow_open = tk.StringVar(), False
        self.box = tk.Tk()
        self.box.attributes("-alpha", 0, "-topmost", True)
        self.box.overrideredirect(True)
        self.box.geometry(f"200x40+{self.x + 72}+{self.y}")
        self.chat_label = tk.Label(self.box, text='asdf', font=("Helvetica", 11), fg="black", wraplength=300)
        self.chat_label.pack()
        self.messages = [{"role": "system",
                          "content": "You are a desktop cat named Lucy. You are 4 years old. Speak like a cat. "
                                     "You can control the computer by suggesting one windows cmd command each time."
                                     "For example, when you are asked to open websites."
                                     "Use one % to separate your speech from the cmd command. "
                                     "For example, to restart the computer, you can say: meow~ %shutdown -r -t 00"
                                     "Your current working directory is C:/Users/USERNAME/, only use relative path in"
                                     "your commands. For example, mkdir .\\Desktop\\hi"
                                     "Do not contain spaces or new lines after the %. Make sure there is only the command and"
                                     "nothing else."}]
        self.w, self.h = 0, 0
        self.is_listening = False
        self.audio_thread = Thread(target=AudioProcessor.s2t, args=(lambda: self.is_listening,))

    def resize(self):
        self.box.update()
        self.w, self.h = self.chat_label.winfo_width(), self.chat_label.winfo_height()
        self.box.geometry(f"{self.w + 50}x{self.h}")

    def event(self, i_frame, state, event_number, x):
        if self.event_number in idle_num:
            self.state = 0
        elif self.event_number == 12:
            self.state = 1
        elif self.event_number in walk_left:
            self.state, self.x = 4, max(0, self.x - 3)
        elif self.event_number in walk_right:
            self.state, self.x = 5, min(screen_width - 72, self.x + 3)
        elif self.event_number in sleep_num:
            self.state = 2
        elif self.event_number == 26:
            self.state = 3

        self.window.after(100 if self.state in {1, 3, 4, 5} else 400, self.update, self.i_frame, self.state, self.event_number, self.x)

    def animate(self, i_frame, array, event_number, a, b):
        self.i_frame = (self.i_frame + 1) % len(array)
        if not self.i_frame:
            self.event_number = randint(a, b)
        return self.i_frame, self.event_number

    def on_double_click(self, event):
        if not self.subwindow_open:
            self.open_subwindow()
            self.subwindow_open = True

    def on_click(self, event):
        self.is_dragging = True
        self.start_x = event.x_root
        self.start_y = event.y_root

    def on_drag(self, event):
        if self.is_dragging is False:
            return
        self.x += event.x_root - self.start_x
        self.y += event.y_root - self.start_y
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.window.geometry(f'72x64+{self.x}+{self.y}')
        self.box.geometry(f"+{self.x + 72}+{self.y}")

    def on_release(self, event):
        self.is_dragging = False
        #self.window.after(1, self.event, self.i_frame, self.state, self.event_number, self.x)

    def open_subwindow(self):
        # Window
        subwindow = tk.Toplevel(self.window)
        subwindow.geometry(f"300x50+{self.x}+{self.y - 50}")
        subwindow.attributes('-topmost', True)
        subwindow.overrideredirect(True)
        subwindow.configure(background='dark gray')

        # Rounded Rectangle
        canvas = tk.Canvas(subwindow, width=300, height=50, bg='dark gray', highlightthickness=0)
        canvas.pack(pady=0)

        radius = 20
        x0, y0, x1, y1 = 10, 10, 270, 40
        canvas.create_arc(x0, y0, x0 + radius, y0 + radius, start=90, extent=90, fill='white', outline='white')
        canvas.create_arc(x1 - radius, y0, x1, y0 + radius, start=0, extent=90, fill='white', outline='white')
        canvas.create_arc(x0, y1 - radius, x0 + radius, y1, start=180, extent=90, fill='white', outline='white')
        canvas.create_arc(x1 - radius, y1 - radius, x1, y1, start=270, extent=90, fill='white', outline='white')
        canvas.create_rectangle(x0 + radius / 2, y0, x1 - radius / 2, y1, fill='white', outline='white')
        canvas.create_rectangle(x0, y0 + radius / 2, x1, y1 - radius / 2, fill='white', outline='white')

        # Textbox
        self.textbox = tk.Entry(subwindow, bd=0, bg='white', font=("Arial", 12))
        self.textbox.place(x=25, y=15, width=230, height=20)
        self.textbox.insert(0, "Say hi to your cat:")
        self.textbox.bind("<FocusIn>", self.clear_placeholder)
        self.textbox.bind("<FocusOut>", self.set_placeholder)
        self.textbox.bind("<Return>", lambda event: self.get_message(subwindow))

    def get_message(self, subwindow):
        self.message.set(self.textbox.get())
        self.close_subwindow(subwindow)
        self.respond(self.message.get())

    def close_subwindow(self, subwindow):
        self.subwindow_open = False
        subwindow.destroy()

    def set_placeholder(self, event):
        if not self.textbox.get():
            self.textbox.insert(0, "Say hi to your cat:")
            # self.textbox.configure(fg='gray')

    def clear_placeholder(self, event):
        # Function to clear placeholder text when textbox is focused
        if self.textbox.get() == "Say hi to your cat:":
            self.textbox.delete(0, tk.END)

    def respond(self, msg):
        response = self.chat.chat.completions.create(
            messages=self.messages + [{'role': 'user', 'content': msg}],
            model="gpt-4o"
        )
        output = response.choices[0].message.content.split('%')
        print(output)
        response_text = output[0]
        if len(output) == 2:
            cmd = output[1]
            out = subprocess.Popen(cmd, shell=True, cwd=PATH, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(out.stdout.read().decode('gbk'))
        self.messages += [{'role': 'user', 'content': msg}, {'role': 'assistant', 'content': '%'.join(output)}]
        self.box.geometry("1920x1080")
        self.chat_label.config(text=response_text)
        self.resize()
        self.box.attributes('-alpha', 0.8)
        self.timer.begin()

    def pos_bound(self):
        if self.y > work_height:
            self.y = work_height
        elif self.y < 0:
            self.y = 0
        if self.x > screen_width - 40:
            self.x = screen_width - 40
        elif self.x < 40:
            self.x = 40

    def update(self, i_frame, state, event_number, x):
        animations = [
            (self.idle, self.event_number, 1, 18), (self.idle_to_sleeping, self.event_number, 19, 19),
            (self.sleeping, self.event_number, 19, 26), (self.sleeping_to_idle, self.event_number, 1, 1),
            (self.walking_left, self.event_number, 1, 18), (self.walking_right, self.event_number, 1, 18)
        ]
        self.frame = animations[state][0][self.i_frame]
        self.i_frame, self.event_number = self.animate(self.i_frame, *animations[state])

        if self.timer.check() > 20:
            self.box.attributes('-alpha', 0)
        if keyboard.is_pressed(LISTEN_KEY):
            if self.is_listening is False:
                self.audio_thread = Thread(target=AudioProcessor().s2t, args=(lambda: self.is_listening,))
                self.audio_thread.start()
                self.is_listening = True
        else:
            if self.is_listening is True:
                self.is_listening = False
                msg = self.audio_thread.join()
                print('Audio Joined:', msg)
                self.respond(msg)

        self.pos_bound()
        self.window.geometry(f'72x64+{self.x}+{self.y}')
        self.box.geometry(f"+{self.x + 72}+{self.y}")
        self.label.configure(image=self.frame)
        self.window.after(1, self.event, self.i_frame, self.state, self.event_number, self.x)


if __name__ == '__main__':
    ket = Ket()
    ket.window.mainloop()