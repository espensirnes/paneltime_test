#!/usr/bin/env python
# -*- coding: utf-8 -*-


import numpy as np
import pandas as pd
import os

N = 1
T = 1000
k = 2
I = np.diag(np.ones(T))
ZERO = I*0
AR = 0.3
MA = 0.3
RANDOM_EFFECT_VOL = 0
RESIDUAL_VOL = 1
SAMP_SIZE = 1000
DIRECTORY = 'simulations'

#Defining the fixed ARMA and GARCH matrices

def lag_matr(L,args):
	k=len(args)
	L=1*L
	r=np.arange(len(L))
	for i in range(k):
		d=(r[i+1:],r[:-i-1])
		L[d]=args[i]
	return L

M_AR=lag_matr(I,[-AR,AR]) #AR means process
M_MA=lag_matr(I,[AR,-AR]) #MA means process
M_MA_1=np.linalg.inv(M_MA)
M_MA_1AR=np.dot(M_MA_1,M_AR)
M_AR_1MA=np.linalg.inv(M_MA_1AR)

V_AR=-lag_matr(-I,[MA, -0.5*MA]) #MA variance process
V_MA=lag_matr(ZERO,[MA, -0.5*MA]) #AR variance process
V_AR_1=np.linalg.inv(V_AR)
V_AR_1MA=np.dot(V_AR_1,V_MA)


#Creating conversion matrices:

def main():

	save_settings()
	for i in range(SAMP_SIZE):
		print(f"Creating sample {i}")
		create_sample(i)	
		

def save_settings():
	if not os.path.exists(DIRECTORY):
		os.makedirs(DIRECTORY)	
	f = open(f"{DIRECTORY}/settings.txt",'w')
	d = dict(globals())
	for k in d:
		if ((not '__' in k) and (not type(d[k])==np.ndarray) and 
			(not k in ['np', 'pd', 'os'])):
			f.write(f"{k}:{d[k]}\n\n")
	f.close()


def create_sample(sid):
	#Generating random variables:
	X0=np.random.normal(size=(T,N,k))
	u0=RESIDUAL_VOL*np.random.normal(size=(T,N,1))
	
	#Adding random effects:
	X0=RE(X0, RANDOM_EFFECT_VOL)
	u0=RE(u0, RANDOM_EFFECT_VOL)
	
	print("Adding ARMA:")
	X1=ARMA(X0)
	u1=ARMA(u0)
	

	print("Adding GARCH:")
	X2, sigma = GARCH(X1)
	u2, _= GARCH(u1, sigma)

	print("Creating variables:")
	Y2=np.sum(X2,2).reshape((T,N,1))+u2
	Y1=np.sum(X1,2).reshape((T,N,1))+u1
	Y0=np.sum(X0,2).reshape((T,N,1))+u0
	IDs=np.arange(N).reshape((1,N,1))*np.ones((T,1,1))
	dates=np.arange(T).reshape((T,1,1))*np.ones((1,N,1))
	

	X2=np.concatenate(X2,0).reshape((N*T,k))
	X1=np.concatenate(X1,0).reshape((N*T,k))
	X0=np.concatenate(X0,0).reshape((N*T,k))

	
	#Saving sample
	df={}
	for i in range(k):
		df[f'X{i}']=X2[:,i]
		df[f'X1{i}']=X1[:,i] 
		df[f'X0{i}']=X0[:,i] 
		
	df['Y']=Y2.flatten()
	df['Y1']=Y1.flatten()
	df['Y0']=Y0.flatten()
	
	df['u']=u2.flatten()
	df['u1']=u1.flatten()
	df['u0']=u0.flatten()
	
	df['IDs']=IDs.flatten()
	df['dates']=dates.flatten()
	df['sigma']=sigma.flatten()
	df['M_MA_1AR'] = np.array([M_MA_1AR[:,0][::-1] for i in range(N)]).flatten()
	df['V_AR_1MA'] = np.array([V_AR_1MA[:,0][::-1] for i in range(N)]).flatten()
	df=pd.DataFrame(df)
	
	fname = f"{DIRECTORY}/data{sid}."
	df.to_pickle(fname+'df')
	df.to_csv(fname+'csv')




#creating random variables:

def RE(X,vol):
	"Returns X after RE, ARIMA and GARCH "
	X_RE_t=vol*np.random.normal(size=(T,1,1))
	X_RE_i=vol*np.random.normal(size=(1,N,1))
	X_RE=X+X_RE_t+X_RE_i
	return X_RE


def ARMA(X):
	X_ARMA=np.array([
      np.dot(M_MA_1AR,X[:,i,:]) 
            for i in range(N)
  ])
	X_ARMA=np.swapaxes(X_ARMA, 0,1)
	return X_ARMA


def GARCH(X, sigma = None):
	if sigma is None:
		sigma0=np.random.normal(size=(T,N,1))
		sigma=np.array([
			np.dot(V_AR_1MA,
						   sigma0[:,i,:]) 
					for i in range(N)
		])
		sigma=1 + np.exp(np.swapaxes(sigma, 0,1))
		sigma = sigma/np.std(sigma, ddof=1)
	X_GARCH=X*sigma
	return X_GARCH, sigma


	
	
main()