#!/usr/bin/env python

import datetime
import scipy.io.wavfile
from scipy import signal
import matplotlib.pyplot as plt
import numpy as np
import math
import io
import csv
from decimal import *
from matplotlib.backends.backend_pdf import PdfPages

data_file = "data/all_clusters.csv"
expansion_num = 10    #Expands the avg_values array by this multiple

file_type = data_file.split(".")[1]
wav_file_name = data_file.split("/")[1].split(".")[0]+".wav"
pdf_file_name = "spectrogram.pdf"
in_file = io.open(data_file,"r")
log_file = io.open("log.txt","a")
energy_values = []
#avg_values = []    #Stores the average energy value from each frame
avg_values_no_zeros = []    #Contains all nonzero avg_values
zero_frames = []    #Stores the frame numbers that have no hits
nonzero_frames = []    #Stores the frame numbers that have hits
frame_values_with_avg_values = []    #Stores lists with each frame value and its respective avg_energy
frame_values_with_avg_values_string = ""
nonzero_frames_string = ""
zero_frames_string = ""
ts = str(datetime.datetime.utcnow())    #Gets the time at execution in UTC


#---log.txt entry header
log_file.write("---Begin Log Entry---".decode("utf-8")+"\n\n")
log_file.write("pmf file: "+(data_file.split("/")[1]).decode("utf-8")+"\n")
log_file.write("Time of execution: "+ts.decode("utf-8")+" UTC \n")


#Removes garbage at end of pmf file
if file_type == "pmf":
    lines = in_file.readlines()    #Contains all the pmf's frames
    del lines[-1]
    in_file.seek(0)    #Returns to the top of in_file


#Determine total number of frames within the given pmf file
def get_frame_count():
    global number_of_frames
    number_of_frames = len(lines)/256

    return number_of_frames


#Isolates a single 256x256 pixel frame from the pmf file
def find_frame_and_avg_energy():
    count = 0
    frame = []
    total_energy = 0
    pixel_count = 0
    while count < 256:
        line = in_file.readline()
        line = line.strip("\n")
        line = line.split(" ")
        frame.append(line)

        for pixel in line:
            if long(pixel) != 0:
                total_energy += long(pixel)
                pixel_count += 1

        count+=1

    if pixel_count == 0:
        return frame, 0
        
    frame_avg_energy = total_energy/pixel_count
        
    return frame, frame_avg_energy


#---Process frames
def process_frames():
    frame_count = get_frame_count()
    with open("avg_values.csv","w") as ofile: 
        #writer = csv.writer(ofile, delimiter=" ")
        #writer.writerow(("Frame# AvgEnergy").split(" "))

        for frame_number in range(frame_count):
            count = 0
            frame, energy = find_frame_and_avg_energy()
            #writer.writerow((str(frame_number+1)+" "+str(energy)).split(" "))

            #---Expands the size of the avg_values array
            while count < expansion_num:
                energy_values.append(energy)#math.log(energy+0.000000001))
                count += 1

            if energy != 0:
                nonzero_frames.append(frame_number+1)
                avg_values_no_zeros.append(energy)
            else:
                zero_frames.append(frame_number+1)

            #print("Frame: ["+str((frame_number+1))+"] Avg_Energy: ["+str(energy)+"]")
            print("Remaining frames: "+str(frame_count-frame_number))

    nonzero_frames_string = str(nonzero_frames)
    zero_frames_string = str(zero_frames)

    #---Create a list of lists where each element is a list of a frame and its avg value
    for index in range(0, len(nonzero_frames)):
        temp = [str(nonzero_frames[index]), str(avg_values_no_zeros[index]).strip("L")]
        frame_values_with_avg_values.append(map(int,temp))
    frame_values_with_avg_values_string = str(frame_values_with_avg_values)
    print("Number of frames with a hit: "+str(len(nonzero_frames)))
    log_file.write("Number of frames with a hit: "+str(len(nonzero_frames)).decode("utf-8")+"\n")
    print("Number of frames without a hit: "+str(len(zero_frames)))
    log_file.write("Number of frames without a hit: "+str(len(zero_frames)).decode("utf-8")+"\n")
    log_file.write("Total number of frames: "+str(len(nonzero_frames)+len(zero_frames)).decode("utf-8")+"\n")


def all_clusters():
    number_of_lines = 0
    for line in in_file:
        energy_values.append(float(line.split(",")[3]))
        number_of_lines += 1
        print("Cluster: "+str(number_of_lines))

    return number_of_lines


#---Repetition function (ideal for very small data sets)
#avg_values_long = []
#count = 0
#while count < 10:
#    for x in avg_values:
#        avg_values_long.append(x)
#    count+=1
#    #print("Count: " + str(count))
#avg_values = avg_values_long
##print(avg_values)


if file_type == "pmf":
    process_frames()

else:
    if file_type == "csv":
        number_of_frames = all_clusters()    #Even though it's called number of frames, it's really number of lines. I'm just reusing a variable instead of creating another one
        

     
#---Create .wav file
print("Creating audio file...")
energy_array = np.asarray(energy_values, dtype=np.int16) ** 1   #The values to be converted to frequencies
fs = 100 * max(energy_array)
log_file.write("Sampling frequency: "+str(fs).decode("utf-8")+" Hz\n")
scipy.io.wavfile.write(wav_file_name, int(fs), energy_array)    #Generates .wav file
length = Decimal(len(energy_values))/Decimal(fs)    #Length of the .wav file in seconds
print("Length of wav file: "+str(length)+" seconds.")
log_file.write("Audio file saved to \""+wav_file_name.decode("utf-8")+"\"\n")
log_file.write("Length of generated .wav file: "+str(length).decode("utf-8")+" s\n")


#---Generate spectrogram
print("Generating spectrogram...")
f = np.asarray(energy_array, dtype=np.int16)
t = np.arange(0.0, float(length), (float(length)/len(f)))
fig_size=[90,20]    #Set size of graph
plt.rcParams["figure.figsize"] = fig_size
plt.rcParams["image.cmap"] = "plasma"
frame_num = np.arange(0.0, float(number_of_frames), float(max(t))/float(number_of_frames))
fig,ax = plt.subplots()
const = []
for x in range(len(frame_num)):
    const.append(fs/4)
plot1 = plt.specgram(f, NFFT=expansion_num, Fs = fs, noverlap=0, pad_to=expansion_num/2)
plt.savefig(pdf_file_name, bbox_inches="tight")
log_file.write("Spectrogram save to \""+pdf_file_name.decode("utf-8")+"\"\n")
line, = plt.plot(frame_num, const, marker=".")
#print(plot1[0][0])

#---Set axis bounds and labels
plt.xlim(min(t), max(t))
plt.ylabel("Frequency [Hz]")
plt.xlabel("Time [sec]")

#####################
#---Cursor event code borrowed from a user response to a stackoverflow question
#https://stackoverflow.com/questions/7908636/possible-to-make-labels-appear-when-hovering-over-a-point-in-matplotlib
#---Begin borrowed code:

annot = ax.annotate("", xy=(0,0), xytext=(-20,20),textcoords="offset points",
                    bbox=dict(boxstyle="round", fc="w"),
                    arrowprops=dict(arrowstyle="-"))
annot.set_visible(False)

def update_annot(ind):
    x,y = line.get_data()
    annot.xy = (x[ind["ind"][0]], y[ind["ind"][0]])
    text = "{}".format(" ".join(list(map(str,ind["ind"]))))
    annot.set_text(text)
    annot.get_bbox_patch().set_alpha(0.4)


def hover(event):
    vis = annot.get_visible()
    if event.inaxes == ax:
        cont, ind = line.contains(event)
        if cont:
            update_annot(ind)
            annot.set_visible(True)
            fig.canvas.draw_idle()
        else:
            if vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()
                

fig.canvas.mpl_connect("motion_notify_event", hover)

#---End borrowed code
#####################

plt.show()


#List frame numbers with hits and avg energies as well as frames numbers without hits (put at end due to potentially long list)
#log_file.write("Frame numbers with a hit: "+nonzero_frames_string.decode("utf-8")+"\n")
log_file.write("Frame numbers with avg values: "+frame_values_with_avg_values_string.decode("utf-8")+"\n")
log_file.write("Frame numbers without a hit: "+zero_frames_string.decode("utf-8")+"\n")


#---Close log.txt
log_file.write("\n".decode("utf-8"))
log_file.write("---End Log Entry---\n\n\n\n\n".decode("utf-8"))
log_file.close()
