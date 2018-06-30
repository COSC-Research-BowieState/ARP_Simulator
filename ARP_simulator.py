#Jacob Kovarskiy#

import random
import math
import cmath
import numpy as np
import matplotlib.pyplot as plt
import scipy as sp
from scipy import special
pi = math.pi

lambda1 = 0.005 #arrival rate per sample
lambda2 = 0.005 #survival rate per sample
kParam1 = 2 #k-parameter for Erlang/gamma distribution (ON)
kParam2 = 2 #k-parameter for Erlang/gamma distribution (OFF)
var1 = lambda1 #variance parameter for log-normal distribution (ON)
var2 = lambda2 #variance parameter for log-normal distribution (OFF)
N = 30000 #number of samples
occupancy = [0]*N
stateTrans = [] #tracks alternating states [1,0,1,0,1,0,...]
intTimes = [] #tracks intervals
upTimes = []
downTimes = []
intTimesSeq = [] #counts and tracks intervals
upDist = "lnorm"    #'exp', 'erl', or 'lnorm'
downDist = "lnorm"  #'exp', 'erl', or 'lnorm'

#process initialized to "on"

totalTime = 0 #tracks total time generated by the ARP
seqState = 1 #tracks next state to generate

while totalTime < N:
    #generates on sequence
    if seqState:
        #generates random on period
        if upDist=="exp":
            period = math.ceil(random.expovariate(lambda1))
        elif upDist=="erl":
            period = math.ceil(random.gammavariate(kParam1,1/lambda1)) #assumes k=2
        elif upDist=="lnorm":
            trueMu = math.log(((1/lambda1)**2)/math.sqrt((1/var1)+(1/lambda1)**2))
            trueSig = math.sqrt(math.log((1/var1)/((1/lambda1)**2)+1))
            period = math.ceil(random.lognormvariate(trueMu,trueSig)) 
        #period = 5
        
        if (totalTime+period) > N: #makes sure total time isn't exceeded
            occupancy[totalTime:N] = [1]*(N-totalTime)
        else: #appends proper sequence of 1s
            occupancy[totalTime:totalTime+period] = [1]*period
            
        #tracks state transitions and on/off durations    
        stateTrans.append(1)
        intTimes.append(period)
        upTimes.append(period)
        intTimesSeq.append(list(range(1,period+1)))
        seqState = 0
        
    #generates off sequence
    else:
        #generates random off period
        if downDist=="exp":
            period = math.ceil(random.expovariate(lambda2))
        elif downDist=="erl":
            period = math.ceil(random.gammavariate(kParam2,1/lambda2)) #assumes k=2
        elif downDist=="lnorm":
            period = math.ceil(random.lognormvariate(lambda2,var2)) 
        #period = 10
        
        if (totalTime+period) > N: #makes sure total time isn't exceeded
            occupancy[totalTime:N] = [0]*(N-totalTime)
        else: #appends proper sequence of 1s
            occupancy[totalTime:totalTime+period] = [0]*period
        
        #tracks state transitions and on/off durations    
        stateTrans.append(0)
        intTimes.append(period)
        downTimes.append(period)
        intTimesSeq.append(list(range(1,period+1)))
        seqState = 1
        
    totalTime += period
    
seqSize = len(stateTrans) #total number of on and off states
traffic_intensity = sum(occupancy)/N #measures traffic intensity
#measures mean signal interarrival
mean_int = sum(intTimes[0:seqSize-(seqSize%2)]) / ((seqSize-(seqSize%2))/2) 
actual_int = 1/lambda1+1/lambda2 #calculates theoretical interarrival

#reactive predictor "accuracy/error"
predicted = occupancy[0:N-1]
#theoretical accuracy based on lambda parameters
theoAcc = 1-(2/actual_int-1/N)
#accuracy based on measured mean interarrival
expAcc = 1-(2/mean_int-1/N)
#observed accuracy
"""
result = [0]*(N-1)
for i in range(N-1):
    if predicted[i]==occupancy[i+1]:
        result[i]=1
obsAcc = sum(result)/(N-1)
"""
obsAcc = sum([predicted[i]==occupancy[i+1] for i in range(N-1)]) / (N-1)



###input RF signal generation###
dLen = 100 #length of the energy detector
fs = 100e6
time = [i/fs for i in range(N*dLen)]
powerLvl = -40 #power in dBm
amp = math.sqrt((10**(powerLvl/10))/1000 * (2*50)) #sinusoid amplitude
noiseVar = 1e-7 #noisefloor variance (1e-7 places noisefloor around -100 dBm)
noisefloor = [math.sqrt(noiseVar)*random.gauss(0,1) for i in range(N*dLen)]

sineWave = [amp*cmath.exp(1j*2*pi*(10e6)*time[i]) for i in range(N*dLen)] #sine wave at 10 MHz            
#SNR of the signal
SNR = 10*math.log10((sum([abs(sineWave[i])**2 for i in range(N*dLen)])/(dLen*N)) / (sum([abs(noisefloor[i])**2 for i in range(N*dLen)])/(dLen*N)))

#Modulates the sine wave with the occupancy state where each state has dLen samples
occSwitch = [occupancy[math.floor(i/dLen)] for i in range(N*dLen)]
inputRF = [sineWave[i]*occSwitch[i]+noisefloor[i] for i in range(N*dLen)]

P_fa = 0.01 #probability of false alarm

thresh = noiseVar/np.sqrt(dLen)*special.erfinv(P_fa)+noiseVar; 


#Calculates total average power over a sliding window
totalAvgPwr = np.zeros((1,dLen*N-dLen+1));
pwrStates = np.zeros((dLen,dLen*N-dLen+1));
t = dLen*N-dLen+1
for i in range(t):
    totalAvgPwr.itemset(i,sum(np.abs(inputRF[i:i+dLen-1])**2)/dLen)
#    for k in  t:
#        pwrStates.itemset((i,k),i+dLen-1)
    #print(pwrStates[i:,])

#Observed states based on energy detector
obsState = totalAvgPwr > thresh;
plt.figure()
r = np.zeros((1,dLen*N-dLen+1))
for i in range(t):
    r.itemset(i,int(i))
    
ts = np.array([i for i in range(dLen*N-dLen+1)])
s = 10*np.log10(totalAvgPwr)-30

print(r)
plt.subplot(2,1,1)
plt.plot(10*np.log10(thresh*np.ones(np.size(totalAvgPwr)))-30)

#energy detector threshold
#plt.plot(t,s,dLen*N-dLen+1)
plt.title('ARP Simulator')
plt.xlabel('Samples')
plt.ylabel('Total Average Power (dBm)')
plt.show()
plt.subplot(2,1,2)
plt.plot(inputRF[dLen:dLen*N])
plt.title('ARP Simulator')
plt.xlabel('Samples')
plt.ylabel('Amplitude (V)')
plt.show()


#Calculates detection accuracy, false alarm rate, and missed detection rate
#detection accuracy evaluated in terms of soonest detection
#dAcc = sum(obsState==occSwitch(dLen:dLen*N))/(dLen*N-dLen+1);
#coherent detection accuracy with the window jumping by dLen samples
#per observations
#dAcc_coherent = sum(obsState(1:dLen:dLen*N-dLen+1)==occupancy)/N;
#faRate = sum(obsState.*(~occSwitch(dLen:dLen*N)))/(dLen*N-dLen+1);
#mdRate = sum(~(obsState).*occSwitch(dLen:dLen*N))/(dLen*N-dLen+1);