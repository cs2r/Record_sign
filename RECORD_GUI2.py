#!/usr/bin/env python
# -*- coding: utf-8 -*-
from imutils.video.webcamvideostream import BaslerVideoStream
import imutils
from tkinter import *
from tkinter.filedialog import askdirectory
from awesometkinter.bidirender import render_bidi_text
import time, json, pyglet, glob
import pandas as pd
import os
import cv2
import numpy
from PIL import Image
from PyV4L2Camera.camera import Camera
import threading
import subprocess


class RecordGUI:
    def __init__(self, master):
        self.basler_res = (1600, 1080)
        self.basler_frame_rate = 60
        self.ir_res = (800, 600)
        self.ir_frame_rate = 60
        print(cv2.__version__)
        self.master = master
        master.title("RECORD SIGN DATA")
        self.master.geometry("700x420+2240+100")

        self.rec_but = Button(master, text="Start REC", state=DISABLED, command=self.rec)
        self.rec_but.grid(row=5, column=0, sticky=W)

        self.egnor_but = Button(master, text="Egnore", state=DISABLED, command=self.egnore)
        self.egnor_but.grid(row=5, column=0, sticky=E)

        self.check_but = Button(master, text="Check Files", command=self.check)
        self.check_but.grid(row=5, column=2)

        self.open_but = Button(master, text="Open", command=self.open)
        self.open_but.grid(row=5, column=3, sticky=W)

        self.close_button = Button(master, text="Close", command=self.close)
        self.close_button.grid(row=5, column=4, sticky=E)

        self.lb = Listbox(master, selectmode=SINGLE, height=20)
        self.lb.grid(row=1, column=0, rowspan=4, sticky=S)
        self.lb.bind('<<ListboxSelect>>', self.sign_select)

        #self.groupVar = IntVar()

        self.singer_label = Label(master, text="#Signer: ")
        self.singer_label.grid(row=1, column=1, sticky=SE)
        self.signer_var = StringVar()
        self.signer = Entry(master, textvariable=self.signer_var, width=5)
        self.signer.grid(row=1, column=2, sticky=SW)
        self.signer_var.set(1)

        self.rep_label = Label(master, text="#Repetitions: ")
        self.rep_label.grid(row=2, column=1, sticky=NE)
        self.max_rep_var = StringVar()
        self.max_rep = Entry(master, textvariable=self.max_rep_var, width=5)
        self.max_rep.grid(row=2, column=2, sticky=NW)
        self.max_rep_var.set(4)
        self.rep = 1

        self.man = IntVar()
        self.manual_but = Checkbutton(master, text = "Manual", variable = self.man, command=self.manual)
        self.manual_but.grid(row=0, column=0, sticky=W)

        self.filename_label = Label(master, text="File name:")
        self.filename_label.grid(row=0, column=1, sticky=E)
        self.filename = Entry(master, state=DISABLED)
        self.filename.grid(row=0, column=2, sticky=W)

        '''
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
        '''

        self.info1 = StringVar()
        self.label1 = Label(master, textvariable=self.info1)
        self.label1.grid(row=3, column=1, columnspan=5, sticky=SW)
        self.info2 = StringVar()
        self.label2 = Label(master, textvariable=self.info2)
        self.label2.grid(row=4, column=1, columnspan=5, sticky=SW)
        self.info3 = StringVar()
        self.label3 = Label(master, textvariable=self.info3)
        self.label3.grid(row=2, column=1, columnspan=5, sticky=SW)

        self.fourcc = cv2.VideoWriter_fourcc(*'MJPG') #H264
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
        self.detect_face = False
        self.save_dir = "/home/g108/Desktop/Recording/"   #"/media/g108/Recording/"  #

        #self.open()

        IRrecord_th = threading.Thread(target=self.recordingIR)
        IRrecord_th.start()

        basler_record_th = threading.Thread(target=self.basler_recording)
        basler_record_th.start()

        display_th = threading.Thread(target=self.display)
        display_th.start()

        self.animation_th = threading.Thread(target=self.amination_TH)
        self.animation_th.start()




    def open(self):
        self.REFname = askdirectory()
        self.path_to_save = self.save_dir + "Signer_" + self.signer_var.get() + self.REFname[46:]
        if not os.path.exists(self.path_to_save):
            os.makedirs(self.path_to_save)
        self.sign_list = glob.glob(self.REFname + '/*.gif')
        self.lb.delete(0, END)
        self.list_of_signs = []
        for sign in self.sign_list:
            self.list_of_signs.append(sign[len(self.REFname)+1:-4])
            self.lb.insert(END, render_bidi_text(sign[len(self.REFname)+1:-4]))
        self.rec_but.config(state=NORMAL)
        self.lb.select_set(0)
        self.sign_select(NONE)


    def manual(self):
        pyglet.app.exit()
        if self.man.get() == 1:
            self.filename.config(state=NORMAL)
            if self.lb.curselection():
                self.temp = self.lb.curselection()[0]
                self.lb.selection_clear(0, END)
            '''self.x_scale.config(state=NORMAL)
            self.y_scale.config(state=NORMAL)
            self.w_scale.config(state=NORMAL)
            self.h_scale.config(state=NORMAL)
            self.sign_rect[0] = self.x.get()
            self.sign_rect[1] = self.y.get()
            self.sign_rect[2] = self.w.get()
            self.sign_rect[3] = self.h.get()'''
        else:
            self.filename.delete(0, END)
            '''self.x_scale.config(state=DISABLED)
            self.y_scale.config(state=DISABLED)
            self.w_scale.config(state=DISABLED)
            self.h_scale.config(state=DISABLED)'''
            self.filename.config(state=DISABLED)
            if hasattr(self, 'temp'):
                self.lb.select_set(self.temp)


    '''def set_X(self, value):
        self.sign_rect[0] = self.x.get()
    def set_Y(self, value):
        self.sign_rect[1] = self.y.get()
    def set_W(self, value):
        self.sign_rect[2] = self.w.get()
    def set_H(self, value):
        self.sign_rect[3] = self.h.get()'''

    def sign_select(self, arg):
        pyglet.app.exit()
        if self.man.get() == 0 and len(self.lb.curselection()) > 0:
            self.sign_name = self.list_of_signs[self.lb.curselection()[0]]   #  self.lb.get(self.lb.curselection()[0])  #
            self.label3.config(fg='green')
            self.info3.set("Sign Name: << " + render_bidi_text(self.sign_name) + " >>")
            '''print(self.lb.curselection())
            print(self.list_of_signs[self.lb.curselection()[0]])
            print(self.lb.get(self.lb.curselection()[0]))
            print("****************************")'''
    def amination_TH(self):
        window = pyglet.window.Window()
        window.set_location(1300, 0)
        while True:
            time.sleep(1)
            if self.man.get() == 0 and len(self.lb.curselection()) > 0:
                animation = pyglet.image.load_animation(self.sign_list[self.lb.curselection()[0]])
            else:
                animation = pyglet.image.load_animation("/home/g108/PycharmProjects/Record_sign/REF_gif/No_data.gif")
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
                self.record_name = self.sign_name
                self.info1.set("RGB is Recording")
                self.label1.config(fg='blue')
                self.info2.set("IR is Recording")
                self.label2.config(fg='blue')
            else:
                self.rec_but.config(text="Start REC")
                self.record = False
                baslerSave_th = threading.Thread(target=self.saveBasler)
                baslerSave_th.start()
                self.basler_saved = False
                irSave_th = threading.Thread(target=self.saveIR())
                irSave_th.start()
                self.ir_saved = False
                self.rec_but.config(state=DISABLED)
                self.egnor_but.config(state=DISABLED)
        elif self.filename.get() != "":
            if self.record == False:
                self.color = (0, 0, 255)
                self.rec_but.config(text="_Stop REC")
                self.record = True
                self.record_name = self.filename.get()
                self.egnor_but.config(state=NORMAL)
            else:
                self.color = (0, 255, 0)
                self.rec_but.config(text="Start REC")
                self.record = False
                self.record_name = self.filename.get()
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
        self.ir_buffer = []

    def check(self):
        print(os.system("find " + self.save_dir + " -type f -size -2M"))

    def saveBasler(self):
        self.info1.set("Saving RGB To \n" + self.path_to_save + "/" + render_bidi_text(self.record_name.replace(' ', '_')) + '_' + str(self.rep) + '_RGB.avi')
        self.label1.config(fg='red')
        file_name = self.path_to_save + "/" + self.record_name.replace(' ', '_') + '_' + str(self.rep) + '_RGB.avi'
        self.basler_out = cv2.VideoWriter(file_name, self.fourcc, self.basler_frame_rate, self.basler_res)
        time.sleep(0.1)

        if self.rep < int(self.max_rep.get()):
            self.rep += 1
        else:
            self.rep = 1
            if self.lb.curselection()[0] < self.lb.size() - 1:
                temp = self.lb.curselection()[0]
                self.lb.selection_clear(0, END)
                self.lb.select_set(temp + 1)
                self.sign_select(NONE)
            else:
                self.lb.selection_clear(0, END)

        for frame in self.basler_buffer:
            self.basler_out.write(frame)
        self.basler_out.release()
        self.basler_buffer = []
        self.info1.set("RGB SAVED In \n" + render_bidi_text(file_name))
        self.label1.config(fg='green')
        self.rec_but.config(state=NORMAL)

    def saveIR(self):
        self.info2.set("Saving IR to \n" + self.path_to_save + "/" + render_bidi_text(self.record_name.replace(' ', '_')) + '_' + str(self.rep) + '_IR.avi')
        self.label2.config(fg='red')
        file_name = self.path_to_save + "/" + self.record_name.replace(' ', '_') + '_' + str(self.rep) + '_IR.avi'
        self.ir_out = cv2.VideoWriter(file_name, self.fourcc, self.ir_frame_rate, self.ir_res)
        time.sleep(0.1)
        for frame in self.ir_buffer:
            pil_image = Image.frombytes('RGB', self.ir_res, frame, 'raw', 'RGB')
            frame = cv2.cvtColor(numpy.asarray(pil_image), cv2.COLOR_RGB2BGR)
            self.ir_out.write(frame)
        self.ir_out.release()
        self.ir_buffer = []
        self.info2.set("IR SAVED In \n" + render_bidi_text(file_name))
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
        if self.detect_face:
            haar_file = 'haarcascade_frontalface_default.xml'
            face_cascade = cv2.CascadeClassifier(haar_file)
        time.sleep(4)
        font = cv2.FONT_HERSHEY_SIMPLEX
        while(self.stream):
            basler_frame = self.basler_frame.copy()
            basler_frame = imutils.resize(basler_frame, height=240)
            if self.detect_face:
                gray = cv2.cvtColor(basler_frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.5, 4)
                for (x, y, w, h) in faces:
                    cv2.rectangle(basler_frame, (x + int(self.sign_rect[0] * w), y + int(self.sign_rect[1] * h)),
                                  (x + int((self.sign_rect[0] + self.sign_rect[2]) * w) , y + int((self.sign_rect[1] + self.sign_rect[3]) * h)),
                                  self.color, 4)
            cv2.putText(basler_frame, self.basler_fps, (5, 15), font, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
            if self.record:
                cv2.putText(basler_frame, self.ir_fps, (5, 30), font, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                cv2.imshow('Display',basler_frame)
                cv2.waitKey(30)
            else:
                ir_frame = self.ir_frame
                pil_image = Image.frombytes('RGB', self.ir_res, ir_frame, 'raw', 'RGB')
                ir_frame = cv2.cvtColor(numpy.asarray(pil_image), cv2.COLOR_RGB2BGR)
                ir_frame = imutils.resize(ir_frame, height=240)
                cv2.putText(ir_frame, self.ir_fps, (5,15), font, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                frame = numpy.concatenate((ir_frame, basler_frame), axis=1)
                cv2.imshow('Display',frame)
                cv2.waitKey(100)
        cv2.destroyAllWindows()
        self.master.destroy()

root = Tk()
rec = RecordGUI(root)
root.mainloop()