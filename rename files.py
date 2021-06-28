import os, glob

sign_list = glob.glob("/home/g108/Desktop/REF_gif/test/*.gif")
for file in sign_list:
    os.rename(file, file[:len(file)-11]+'.gif')