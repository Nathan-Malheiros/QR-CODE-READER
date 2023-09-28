import cv2
import qrcode
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import time
from datetime import datetime

class QRCodeReaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Code Reader")

        self.cap = None
        self.is_reading = False
        self.last_read_time = None
        self.qr_code_history = {}  # Dicionário para rastrear QR codes lidos e seus horários
        self.first_read_time = None

        self.label = tk.Label(root)
        self.label.pack()

        self.result_label = tk.Label(root, text="", wraplength=300)
        self.result_label.pack()

        self.time_difference_label = tk.Label(root, text="Diferença de tempo: N/A")
        self.time_difference_label.pack()

        self.history_text = tk.Text(root, height=10, width=40)
        self.history_text.pack()

        self.quit_button = tk.Button(root, text="Sair", command=self.quit)
        self.quit_button.pack()

        self.start_button = tk.Button(root, text="Iniciar", command=self.start_reading)
        self.start_button.pack()

        self.stop_button = tk.Button(root, text="Parar", command=self.stop_reading, state=tk.DISABLED)
        self.stop_button.pack()

        self.clock_label = tk.Label(root, text="", font=("Helvetica", 16))
        self.clock_label.pack()

    def quit(self):
        if self.cap is not None:
            self.cap.release()
        self.root.quit()

    def start_reading(self):
        if not self.is_reading:
            self.cap = cv2.VideoCapture(0)
            self.is_reading = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.result_label.config(text="")  # Limpa o texto de resultado
            self.qr_code_history = {}  # Limpa o histórico
            self.first_read_time = None
            self.last_read_time = None
            self.history_text.delete("1.0", tk.END)  # Limpa a área de texto
            self.label.pack()  # Exibe o widget da imagem da câmera
            self.read_qr_code()

    def stop_reading(self):
        if self.is_reading:
            self.is_reading = False
            if self.cap is not None:
                self.cap.release()  # Libera a câmera
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.result_label.config(text="Leitura interrompida.")
            self.label.pack_forget()  # Oculta o widget da imagem da câmera

    def read_qr_code(self):
        if self.is_reading:
            current_time = time.time()
            if self.last_read_time is None or (current_time - self.last_read_time.timestamp()) >= 2:
                if self.cap is None or not self.cap.isOpened():
                    self.cap = cv2.VideoCapture(0)  # Reabra a câmera se estiver fechada
                ret, frame = self.cap.read()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                detector = cv2.QRCodeDetector()
                retval, decoded_info, points, straight_qrcode = detector.detectAndDecodeMulti(gray)

                if retval:
                    for info in decoded_info:
                        if info not in self.qr_code_history:
                            self.qr_code_history[info] = [datetime.now()]
                        else:
                            self.qr_code_history[info].append(datetime.now())  # Adicione o horário ao histórico

                        if self.first_read_time is None:
                            self.first_read_time = datetime.now()
                        self.last_read_time = datetime.now()

                    self.result_label.config(text="Conteúdo do QR Code:\n" + "\n".join(decoded_info))  # Exibe o conteúdo do QR code
                    self.update_history_text()  # Atualize o histórico na área de texto
                    self.update_time_difference()  # Atualize a diferença de tempo
                else:
                    self.result_label.config(text="Nenhum QR Code detectado.")

                self.display_frame(frame)
                self.update_clock()  # Atualize o relógio
            self.root.after(10, self.read_qr_code)

    def display_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, _ = frame.shape

        # Redimensione a imagem da câmera para caber no espaço disponível mantendo a proporção
        max_height = 320
        max_width = 240
        if height > max_height or width > max_width:
            scale = min(max_height / height, max_width / width)
            frame = cv2.resize(frame, (int(width * scale), int(height * scale)))

        image = Image.fromarray(frame)
        image = ImageTk.PhotoImage(image=image)
        self.label.config(image=image)
        self.label.image = image

    def update_history_text(self):
        # Limpe o conteúdo atual da área de texto
        self.history_text.delete("1.0", tk.END)

        # Adicione os QR codes lidos e seus horários ao histórico na área de texto
        for qr_code, timestamps in self.qr_code_history.items():
            for timestamp in timestamps:
                self.history_text.insert(tk.END, f"{timestamp}: {qr_code}\n")

    def update_clock(self):
        # Obtenha a hora atual no formato HH:MM:SS
        current_time = datetime.now().strftime("%H:%M:%S")
        self.clock_label.config(text=current_time)

    def update_time_difference(self):
        # Calcule a diferença de tempo apenas para os QR codes que foram lidos mais de uma vez
        if self.first_read_time:
            for qr_code, timestamps in self.qr_code_history.items():
                if len(timestamps) > 1:
                    time_difference = timestamps[-1] - timestamps[0]
                    minutes, seconds = divmod(time_difference.seconds, 60)
                    hours, minutes = divmod(minutes, 60)
                    self.history_text.insert(tk.END, f"{qr_code} - Diferença de tempo: {hours} horas, {minutes} minutos\n")
                    self.history_text.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = QRCodeReaderApp(root)
    root.mainloop()
