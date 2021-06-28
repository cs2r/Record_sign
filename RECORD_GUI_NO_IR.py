#!/usr/bin/env python
# -*- coding: utf-8 -*-
from imutils.video.webcamvideostream import BaslerVideoStream
import imutils
from tkinter import *
import time, json, pyglet, glob
import cv2
import numpy
from PIL import Image
from PyV4L2Camera.camera import Camera
import threading


class RecordGUI:
    def __init__(self, master):
        self.basler_res = (1600, 1080)
        self.basler_frame_rate = 60
        self.ir_res = (800, 600)
        self.ir_frame_rate = 60
        print(cv2.__version__)
        self.master = master
        master.title("RECORD SIGN DATA")
        self.master.geometry("680x400+600+700")

        self.rec_but = Button(master, text="Start REC", command=self.rec)
        self.rec_but.grid(row=5, column=0, sticky=W)

        self.egnor_but = Button(master, text="Egnore", state=DISABLED, command=self.egnore)
        self.egnor_but.grid(row=5, column=0, sticky=E)

        self.close_button = Button(master, text="Close", command=self.close)
        self.close_button.grid(row=5, column=3, sticky=E)

        self.sign_list = glob.glob("/home/g108/Desktop/REF/last/*.gif")

        self.lb = Listbox(master, selectmode=SINGLE, height=20)
        self.lb.grid(row=0, column=0, rowspan=5)
        for sign in self.sign_list:
            self.lb.insert(END, sign[28:])
        self.lb.bind('<<ListboxSelect>>', self.sign_select)



        self.man = IntVar()
        self.manual_but = Checkbutton(master, text = "Manual", variable = self.man, command=self.manual)
        self.manual_but.grid(row=0, column=1, sticky=W)

        self.filename_label = Label(master, text="File name:")
        self.filename_label.grid(row=0, column=2, sticky=E)
        self.filename = Entry(master, state=DISABLED)
        self.filename.grid(row=0, column=3, sticky=W)

        self.x = DoubleVar()
        self.x_scale = Scale(master, from_=-3, to=3, orient=HORIZONTAL, label="X", resolution=0.1 ,length=500, variable=self.x, command=self.set_X)
        self.x_scale.grid(row=1, column=1, columnspan=3)
        self.x_scale.set(0.0)
        self.x_scale.config(state=DISABLED)

        self.y = DoubleVar()
        self.y_scale = Scale(master, from_=-3, to=3, orient=HORIZONTAL, label="Y", resolution=0.1 ,length=500, variable=self.y, command=self.set_Y)
        self.y_scale.grid(row=2, column=1, columnspan=3)
        self.y_scale.set(0.0)
        self.y_scale.config(state=DISABLED)

        self.w = DoubleVar()
        self.w_scale = Scale(master, from_=0, to=5, orient=HORIZONTAL, label="W", resolution=0.1 ,length=500, variable=self.w, command=self.set_W)
        self.w_scale.grid(row=3, column=1, columnspan=3)
        self.w_scale.set(1.0)
        self.w_scale.config(state=DISABLED)

        self.h = DoubleVar()
        self.h_scale = Scale(master, from_=0, to=5, orient=HORIZONTAL, label="H", resolution=0.1 ,length=500, variable=self.h, command=self.set_H)
        self.h_scale.grid(row=4, column=1, columnspan=3)
        self.h_scale.set(1.0)
        self.h_scale.config(state=DISABLED)

        self.info1 = StringVar()
        self.label1 = Label(master, textvariable=self.info1)
        self.label1.grid(row=5, column=1, sticky=W)
        self.info2 = StringVar()
        self.label2 = Label(master, textvariable=self.info2)
        self.label2.grid(row=5, column=2, sticky=W)
        self.info3 = StringVar()
        self.label3 = Label(master, textvariable=self.info3)
        self.label3.grid(row=5, column=3, sticky=W)

        self.fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        self.record = False
        self.color = (0, 255, 0)

        self.basler_buffer = []
        self.ir_buffer = []

        self.basler_fps = ''
        self.ir_fps = ''

        self.stream = True
        self.sign_rect = [0, 0, 1, 1]
        self.sign_name = ""

        self.basler_saved = False
        self.ir_saved = False

        #IRrecord_th = threading.Thread(target=self.recordingIR)
        #IRrecord_th.start()

        basler_record_th = threading.Thread(target=self.basler_recording)
        basler_record_th.start()

        display_th = threading.Thread(target=self.display)
        display_th.start()

        self.animation_th = threading.Thread(target=self.amination_TH)
        self.animation_th.start()
        self.lb.select_set(0)
        self.sign_select(NONE)



    def manual(self):
        if self.man.get() == 1:
            self.lb.selection_clear(0, END)
            self.filename.config(state=NORMAL)
            self.x_scale.config(state=NORMAL)
            self.y_scale.config(state=NORMAL)
            self.w_scale.config(state=NORMAL)
            self.h_scale.config(state=NORMAL)
            self.sign_rect[0] = self.x.get()
            self.sign_rect[1] = self.y.get()
            self.sign_rect[2] = self.w.get()
            self.sign_rect[3] = self.h.get()
        else:
            self.x_scale.config(state=DISABLED)
            self.y_scale.config(state=DISABLED)
            self.w_scale.config(state=DISABLED)
            self.h_scale.config(state=DISABLED)
            self.filename.config(state=DISABLED)

    def set_X(self, value):
        self.sign_rect[0] = self.x.get()
    def set_Y(self, value):
        self.sign_rect[1] = self.y.get()
    def set_W(self, value):
        self.sign_rect[2] = self.w.get()
    def set_H(self, value):
        self.sign_rect[3] = self.h.get()

    def sign_select(self, arg):
        pyglet.app.exit()
        if self.lb.curselection()!=[]:
            self.sign_name = self.lb.get(self.lb.curselection()[0])

    def amination_TH(self):
        window = pyglet.window.Window()
        while True:
            time.sleep(1)
            animation = pyglet.image.load_animation(self.sign_list[self.lb.curselection()[0]])
            animSprite = pyglet.sprite.Sprite(animation)
            w = animSprite.width
            h = animSprite.height
            window.width = w
            window.height = h
            r, g, b, alpha = 0.5, 0.5, 0.8, 0.5

            pyglet.gl.glClearColor(r, g, b, alpha)

            @window.event
            def on_draw():
                window.clear()
                animSprite.draw()
            pyglet.app.run()

    def close(self):
        pyglet.app.exit()
        self.stream = False
        self.master.destroy()

    def rec(self):
        if self.lb.curselection():
            if self.record == False:
                self.color = (0, 0, 255)
                self.rec_but.config(text="_Stop REC")
                self.egnor_but.config(state=NORMAL)
                self.record = True
                self.record_name = self.sign_name[:-4]
            else:
                self.color = (0, 255, 0)
                self.rec_but.config(text="Start REC")
                self.record = False
                baslerSave_th = threading.Thread(target=self.saveBasler)
                baslerSave_th.start()
                self.basler_saved = False
                irSave_th = threading.Thread(target=self.saveIR())
                irSave_th.start()
                self.ir_saved = False
                self.rec_but.config(state = DISABLED)
                self.egnor_but.config(state=DISABLED)
                if self.lb.curselection() [0] < self.lb.size()-1:
                    temp = self.lb.curselection()[0]
                    self.lb.selection_clear(0, END)
                    self.lb.select_set(temp+1)
                    self.sign_select(NONE)
                else:
                    self.lb.selection_clear(0, END)
        elif self.filename.get() != "":
            if self.record == False:
                self.color = (0, 0, 255)
                self.rec_but.config(text="_Stop REC")
                self.record = True
                self.egnor_but.config(state=NORMAL)
            else:
                self.color = (0, 255, 0)
                self.rec_but.config(text="Start REC")
                self.record = False
                self.sign_name = self.filename.get()
                baslerSave_th = threading.Thread(target=self.saveBasler)
                baslerSave_th.start()
                self.basler_saved = False
                irSave_th = threading.Thread(target=self.saveIR)
                irSave_th.start()
                self.ir_saved = False
                self.rec_but.config(state=DISABLED)
                self.egnor_but.config(state=DISABLED)
        else:
            print("Please select the sign to record")

    def egnore(self):
        self.info1.set("EGNORED")
        self.label1.config(fg='yellow')
        self.info2.set("EGNORED")
        self.label2.config(fg='yellow')
        self.egnor_but.config(state=DISABLED)

        self.color = (0, 255, 0)
        self.rec_but.config(text="Start REC")
        self.record = False
        self.basler_buffer = []





    def saveBasler(self):
        self.info1.set("Saving Basler...")
        self.label1.config(fg='red')
        self.basler_out = cv2.VideoWriter("/home/g108/Desktop/recording/" + self.record_name + '_BASLER.avi', self.fourcc, self.basler_frame_rate, self.basler_res)
        time.sleep(0.1)
        for frame in self.basler_buffer:
            self.basler_out.write(frame)
        self.basler_out.release()
        self.basler_buffer = []
        self.info1.set("BASLER SAVED")
        self.label1.config(fg='green')
        self.rec_but.config(state=NORMAL)


    def saveIR(self):
        self.info2.set("Saving IR...")
        self.label2.config(fg='red')
        #self.ir_out = cv2.VideoWriter("/home/g108/Desktop/recording/" + self.record_name + '_IR.avi', self.fourcc, self.ir_frame_rate, self.ir_res)
        time.sleep(0.1)
        for frame in self.ir_buffer:
            pil_image = Image.frombytes('RGB', self.ir_res, frame, 'raw', 'RGB')
            frame = cv2.cvtColor(numpy.asarray(pil_image), cv2.COLOR_RGB2BGR)
            self.ir_out.write(frame)
        #self.ir_out.release()
        #self.ir_buffer = []
        self.info2.set("IR SAVED")
        self.label2.config(fg='green')

    def basler_recording(self):
        time.sleep(1)
        baslerStream = BaslerVideoStream().start()
        while(self.stream):
            start = time.time()
            Rstart=time.time()

            self.basler_frame = baslerStream.read()
            if (self.record):
                self.basler_buffer.append(self.basler_frame)

            total_time = time.time() - start
            if total_time < 1/self.basler_frame_rate:
                time.sleep(1/self.basler_frame_rate - total_time)
            self.basler_fps = str("Basler_FPS: {:.2f}".format(1/(time.time()-Rstart)))
        baslerStream.stop()
        cv2.destroyAllWindows()
        self.master.destroy()

    def recordingIR(self):
        IRcamera = Camera('/dev/video0', self.ir_res[0], self.ir_res[1])
        while(self.stream):
            start = time.time()
            Rstart=time.time()

            self.ir_frame = IRcamera.get_frame()

            if self.record:
                self.ir_buffer.append(self.ir_frame)

            total_time = time.time() - start

            if total_time < 1/self.ir_frame_rate:
                time.sleep(1/self.ir_frame_rate - total_time)
            self.ir_fps = str("IR_FPS: {:.2f}".format(1/(time.time()-Rstart)))
        IRcamera.close()
        cv2.destroyAllWindows()
        self.master.destroy()

    def display(self):
        haar_file = 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(haar_file)
        time.sleep(4)
        font = cv2.FONT_HERSHEY_SIMPLEX
        while(self.stream):
            basler_frame = self.basler_frame.copy()
            basler_frame = imutils.resize(basler_frame, height=240)
            gray = cv2.cvtColor(basler_frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.5, 4)
            for (x, y, w, h) in faces:
                cv2.rectangle(basler_frame, (x + int(self.sign_rect[0] * w), y + int(self.sign_rect[1] * h)),
                              (x + int((self.sign_rect[0] + self.sign_rect[2]) * w) , y + int((self.sign_rect[1] + self.sign_rect[3]) * h)),
                              self.color, 4)
            cv2.putText(basler_frame, self.basler_fps, (5,15), font, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
            if self.record:
                cv2.putText(basler_frame, self.ir_fps, (5,30), font, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                cv2.imshow('Display',basler_frame)
                cv2.waitKey(30)
            else:
                #ir_frame = self.ir_frame
                #pil_image = Image.frombytes('RGB', self.ir_res, ir_frame, 'raw', 'RGB')
                #ir_frame = cv2.cvtColor(numpy.asarray(pil_image), cv2.COLOR_RGB2BGR)
                #ir_frame = imutils.resize(ir_frame, height=240)
                #cv2.putText(ir_frame, self.ir_fps, (5,15), font, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                #frame = numpy.concatenate((ir_frame, basler_frame), axis=1)
                #cv2.imshow('Display',frame)
                cv2.imshow('Display', basler_frame)
                cv2.waitKey(100)
        cv2.destroyAllWindows()
        self.master.destroy()

root = Tk()
rec = RecordGUI(root)
root.mainloop()