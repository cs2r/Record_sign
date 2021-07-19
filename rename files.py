import os, glob

for root, dirs, files in os.walk("REF_gif"):
    for file in files:
        if root != "REF_gif":
            os.rename(root + '/' + file, root + '/' + file.replace("_1_RGB_converted",""))
            '''if len(file.split('_')) > 4:
                print("_".join(file.split('_')[:-3]) + ".gif")
                os.rename(root + '/' + file, root + '/' + "_".join(file.split('_')[:-3]) + ".gif")
            else:
                os.rename(root + '/' + file, root + '/' + file.split('_')[0] + ".gif")'''
