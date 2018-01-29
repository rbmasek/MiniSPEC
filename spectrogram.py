#!/usr/bin/env python

import time
import datetime
import scipy
import scipy.io.wavfile
from scipy import signal
import matplotlib.pyplot as plt
import numpy as np
import io
import csv
from decimal import *
from matplotlib.backends.backend_pdf import PdfPages

pmf_file = "data/thurs_test35.pmf"
wav_file_name = "space_sounds.wav"
pdf_file_name = "spectrogram.pdf"
in_file = io.open(pmf_file,"r")
log_file = io.open("log.txt","a")
lines = in_file.readlines()    #Contains all the pmf's frames
avg_values = []    #Stores the average energy value from each frame 
zero_frames = []    #Stores the frame numbers that have no hits
nonzero_frames = []    #Stores the frame numbers that have hits
fs = 10000    #Sampling frequency
ts = time.time()    #Gets the time at execution
st = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S" + " CST")    #Translates time to human-readable time


#---log.txt entry header
log_file.write("---Begin Log Entry---".decode("utf-8")+"\n\n")
log_file.write("pmf file: "+(pmf_file.split("/")[1]).decode("utf-8")+"\n")
log_file.write("Time of execution: "+st.decode("utf-8")+"\n")


#---User-set sampling frequency
#fs = raw_input("Set the sampling frequency: ")
log_file.write("Sampling frequency: "+str(fs).decode("utf-8")+" Hz\n")


#Removes garbage at end of pmf file
del lines[-1]


#Determine total number of frames within the given data file
def get_frame_count():
    global number_of_frames
    number_of_frames = len(lines)/256

    return number_of_frames

in_file.seek(0)

#Isolates a single 256x256 pixel frame from the pmf file
def find_frame():
    count = 0
    frame = []
    while count < 256:
        #line = lines[0]
        #del lines[0]
        line = in_file.readline()
        line = line.strip("\n")
        frame.append(line.split(" "))
        count+=1

    return frame


#Finds all non-zero pixel values and averages them over the number of non-zero values
def avg_energy(in_frame):
    total_energy = 0
    pixel_count = 0
    for r in range(256):
        for c in range(256):
            #print(in_frame[r][c])
            if long(in_frame[r][c]) != 0:
                total_energy+=long(in_frame[r][c])
                pixel_count+=1
    if pixel_count == 0:
        return 0
    in_frame_avg_energy = total_energy/pixel_count

    return in_frame_avg_energy


#---Process frames
frame_count = get_frame_count()
with open("avg_values.csv","w") as ofile: 
    writer = csv.writer(ofile, delimiter=" ")
    writer.writerow(("Frame# AvgEnergy").split(" "))
    for frame_number in range(frame_count):
        frame = find_frame()
        avg = avg_energy(frame)
        writer.writerow((str(frame_number+1)+" "+str(avg)).split(" "))
        #if frame_number >= 50 and frame_number <= 90:
        #    avg = avg * 4
        avg_values.append(avg**2)
        if avg != 0:
            nonzero_frames.append(frame_number+1)
        else:
            zero_frames.append(frame_number+1)
        #print("Frame: ["+str((frame_number+1))+"] Avg_Energy: ["+str(avg)+"]")
        print("Remaining frames: "+str(len(lines)/256-len(avg_values)))
nonzero_frames_string = str(nonzero_frames)
zero_frames_string = str(zero_frames)

#---Creates list of avg values without the zeros
avg_values_no_zeros = []
for x in avg_values:
    if x != 0:
        avg_values_no_zeros.append(x)

#---Create a list of lists where each element is a list of a frame and its avg value
frame_values_with_avg_values = []
for index in range(0, len(nonzero_frames)):
    temp = [str(nonzero_frames[index]), str(avg_values_no_zeros[index]).strip("L")]
    frame_values_with_avg_values.append(map(int,temp))
frame_values_with_avg_values_string = str(frame_values_with_avg_values)

print("Number of frames with a hit: "+str(len(nonzero_frames)))
log_file.write("Number of frames with a hit: "+str(len(nonzero_frames)).decode("utf-8")+"\n")
print("Number of frames without a hit: "+str(len(zero_frames)))
log_file.write("Number of frames without a hit: "+str(len(zero_frames)).decode("utf-8")+"\n")
log_file.write("Total number of frames: "+str(len(nonzero_frames)+len(zero_frames)).decode("utf-8")+"\n")


#---Expands the size of the avg_values array
avg_values_long = []
number_of_increase = 100
for x in range(len(avg_values)):
    count = 0
    while count < number_of_increase:
        avg_values_long.append(avg_values[x])
        count+=1
avg_values = avg_values_long


#---Repetition function
#avg_values_long = []
#count = 0
#while count < 10:
#    for x in avg_values:
#        avg_values_long.append(x)
#    count+=1
#    #print("Count: " + str(count))
#avg_values = avg_values_long
##print(avg_values)


#---Export avg_values to CSV file

#    for x in range(0, avg_values):
#        writer.writerow((x+" "+avg_values[x]).split(" "))

        
#Create .wav file
print("Creating audio file...")
avg_energy_array = np.asarray(avg_values, dtype=np.int16)
scipy.io.wavfile.write(wav_file_name, int(fs), avg_energy_array)
length = Decimal(len(avg_values))/Decimal(fs)
print("Length of wav file: "+str(length)+" seconds.")
log_file.write("Audio file saved to \""+wav_file_name.decode("utf-8")+"\"\n")
log_file.write("Length of generated .wav file: "+str(length).decode("utf-8")+" s\n")


#---Generate spectrogram
print("Generating spectrogram...")
#f, t, Sxx = signal.spectrogram(avg_energy_array, fs)
#plt.pcolormesh(t, f, Sxx)
f = np.asarray(avg_values, dtype=np.int16)
t = np.arange(0.0, float(length), (float(length)/len(f)))
fig_size=[16,16]
plt.rcParams["figure.figsize"] = fig_size
#plt.plot(t,f)

#plt.rcParams["image.cmap"] = "plasma"
frame_num = np.arange(0.0, float(number_of_frames), float(max(t))/float(number_of_frames))
fig,ax = plt.subplots()
const = []
for x in range(len(frame_num)):
    const.append(2500)
line, = plt.plot(frame_num, const, marker=".")
plot1 = plt.specgram(f, NFFT=256, Fs = fs, noverlap=128, pad_to=256)
#plt.savefig(pdf_file_name, bbox_inches="tight")
log_file.write("Spectrogram save to \""+pdf_file_name.decode("utf-8")+"\"\n")
#print(plot1[0][0])

plt.xlim(min(t), max(t))#.6656)
plt.ylabel("Frequency [Hz]")
plt.xlabel("Time [sec]")

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

plt.show()

plot1 = plt.specgram(f, NFFT=256, Fs = fs, noverlap=128, pad_to=256)
plt.savefig(pdf_file_name, bbox_inches="tight")

#log_file.write("Frame numbers with a hit: "+nonzero_frames_string.decode("utf-8")+"\n")
log_file.write("Frame numbers with avg values: "+frame_values_with_avg_values_string.decode("utf-8")+"\n")
log_file.write("Frame numbers without a hit: "+zero_frames_string.decode("utf-8")+"\n")


#---Close log.txt
log_file.write("\n".decode("utf-8"))
log_file.write("---End Log Entry---\n".decode("utf-8"))
log_file.write("\n".decode("utf-8"))
log_file.write("\n".decode("utf-8"))
log_file.write("\n".decode("utf-8"))
log_file.close()

#import wave

#audio = wave.open("output.wav","w")
#audio.writeframesraw(avg_energy)
#audio.close()


#---Example
#data = np.random.uniform(-1,1,44100) # 44100 random samples between -1 and 1
#scaled = np.int16(data/np.max(np.abs(data)) * 32767)
#scipy.io.wavfile.write('test.wav', 44100, scaled)
