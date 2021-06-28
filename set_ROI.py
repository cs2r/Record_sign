#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tkinter import *
from tkinter import filedialog
import time, json
import cv2
import threading

class RoiGUI:
    def __init__(self, master):
        with open("signs_list.json", 'r') as file:
            self.sign_list = json.load(file)

        self.master = master
        master.title("Select ROI from video")
        self.master.geometry("505x277")

        self.text = Label(master, text="Sign name:")
        self.text.grid(row=0, column=0, sticky=E)
        self.sign_name_entry = Entry(master)
        self.sign_name_entry.grid(row=0, column=1, sticky=W)

        self.open_video_but = Button(master, text="Open Video", command=self.open_video)
        self.open_video_but.grid(row=0, column=3, sticky=E)
        self.video_name = 0

        self.x = DoubleVar()
        self.x_scale = Scale(master, from_=-3, to=3, orient=HORIZONTAL, label="X", resolution=0.1 ,length=500, variable=self.x, command=self.set_X)
        self.x_scale.grid(row=1, column=0, columnspan=4)
        self.x_scale.set(0)
        self.y = DoubleVar()
        self.y_scale = Scale(master, from_=-3, to=3, orient=HORIZONTAL, label="Y", resolution=0.1 ,length=500, variable=self.y, command=self.set_Y)
        self.y_scale.grid(row=2, column=0, columnspan=4)
        self.y_scale.set(0)
        self.w = DoubleVar()
        self.w_scale = Scale(master, from_=0, to=5, orient=HORIZONTAL, label="W", resolution=0.1 ,length=500, variable=self.w, command=self.set_W)
        self.w_scale.grid(row=3, column=0, columnspan=4)
        self.w_scale.set(1)
        self.h = DoubleVar()
        self.h_scale = Scale(master, from_=0, to=5, orient=HORIZONTAL, label="H", resolution=0.1 ,length=500, variable=self.h, command=self.set_H)
        self.h_scale.grid(row=4, column=0, columnspan=4)
        self.h_scale.set(1)

        self.save_button = Button(master, text="Save Setting", command=self.save)
        self.save_button.grid(row=0, column=2, sticky=W)

        self.close_button = Button(master, text="Close", command=self.close)
        self.close_button.grid(row=5, column=3, sticky=E)
        self.stream = False
        self.stop = False
        self.t = threading.Thread(target=self.streaming)
        self.t.start()

        self.next_but = Button(master, text=">>", command=self.playforward)
        self.next_but.grid(row=5, column=2)

        self.pause_but = Button(master, text="Pause", command=self.play_pause)
        self.pause_but.grid(row=5, column=1)
        self.pause = False

        self.previous_but = Button(master, text="<<", command=self.playback)
        self.previous_but.grid(row=5, column=0)

        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')

        self.sign_rect = [0, 0, 1, 1]
        self.sign_name = ""
        self.color = (0, 255, 0)

    def open_video(self):
        self.video_name = filedialog.askopenfilename(initialdir = "~/PycharmProjects/recording",title = "Select the video file")
        if self.video_name:
            self.cap = cv2.VideoCapture(self.video_name)
            self.stream = True
        else:
            print("Please select the video file")

    def play_pause(self):
        if self.pause == False:
            self.pause = True
            self.pause_but.config(text="Play")
        else:
            self.pause = False
            self.pause_but.config(text="Pause")

    def playforward(self):
        i = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        if i+10 < self.cap.get(cv2.CAP_PROP_FRAME_COUNT):
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, i+20)
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def playback(self):
        i = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        if i-10 > 0:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, i-20)
        else:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def set_X(self, value):
        self.sign_rect[0] = self.x.get()
    def set_Y(self, value):
        self.sign_rect[1] = self.y.get()
    def set_W(self, value):
        self.sign_rect[2] = self.w.get()
    def set_H(self, value):
        self.sign_rect[3] = self.h.get()

    def save(self):
        if self.sign_name_entry.get() != "":
            self.sign_list.update({self.sign_name_entry.get(): [self.x_scale.get(), self.y_scale.get(), self.w_scale.get(), self.h_scale.get()]})
            with open("signs_list.json", 'w') as file:
                json.dump(self.sign_list, file)
            self.sign_name_entry.delete(0, END)
        else:
            print("Enter name of the sign")

    def close(self):
        self.stream = False
        self.stop = True


    def streaming(self):
        self.cap = cv2.VideoCapture(self.video_name)
        self.pause = False
        haar_file = 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(haar_file)
        while (True):
            if(self.stream):
                if self.pause == False:
                    ret, frame = self.cap.read()
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.5, 4)
                disp = frame.copy()
                for (x, y, w, h) in faces:
                    cv2.rectangle(disp, (x + int(self.sign_rect[0] * w), y + int(self.sign_rect[1] * h)),
                                  (x + int((self.sign_rect[0] + self.sign_rect[2]) * w) , y + int((self.sign_rect[1] + self.sign_rect[3]) * h)),
                                  self.color, 4)
                cv2.imshow('frame', disp)
                if self.stop or (cv2.waitKey(1) & 0xFF == ord('q')): # quit
                    break
            else:
                print("Please Select The Video Input!!!")
                time.sleep(1)

        self.cap.release()
        cv2.destroyAllWindows()
        time.sleep(1)
        self.master.destroy()

root = Tk()
rec = RoiGUI(root)
root.mainloop()
