import numpy as np
import pandas as pd
from scipy import interpolate
import csv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import ScalarFormatter
from tkinter import *
from tkinter import ttk
import sys
import os
import random

def readinput(filename):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    #print("variableAll")
    #display(csv_input[0:24])
    #print("\n")
    symbol = csv_input['Symbol']
    value = csv_input['Value']
    valueDict = {}
    for i, j in zip(symbol, value):
        valueDict[i] = float(j)
    return csv_input, valueDict

def CeqLHVFunc(filename,fuelName):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    #print("CeqLHV")
    #display(csv_input)
    #print("\n")
    fuelType = csv_input['Fuel type']
    CeqLHV = csv_input['CeqLHV']
    fuelDict = {}
    for i, j in zip(fuelType, CeqLHV):
        fuelDict[i] = float(j)
    return fuelDict[fuelName]

def Cco2Func(filename,fuelName):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    #print("Cco2")
    #display(csv_input)
    #print("\n")
    fuelType = csv_input['Fuel type']
    Cco2 = csv_input['Cco2']
    Cco2Dict = {}
    for i, j in zip(fuelType, Cco2):
        Cco2Dict[i] = float(j)
    return Cco2Dict[fuelName]

def initialFleetFunc(filename):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    year = csv_input['Year']
    TEU = csv_input['TEU']
    iniFleetDict = {}
    k = 0
    for i, j in zip(year, TEU):
        iniFleetDict.setdefault(k,{})
        iniFleetDict[k]['year'] = int(i)
        iniFleetDict[k]['TEU'] = float(j)
        k += 1
    return iniFleetDict

def decisionList(filename):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",").fillna(0)
    Year = csv_input['Year']
    Order = csv_input['Order']
    fuelType = csv_input['Fuel type']
    WPS = csv_input['WPS']
    SPS = csv_input['SPS']
    CCS = csv_input['CCS']
    CAP = csv_input['CAP']
    Speed = csv_input['Speed']
    valueDict = {}
    for i, j, k, l, m, n, o, p in zip(Year, Order, fuelType, WPS, SPS, CCS, CAP, Speed):
        valueDict.setdefault(int(i),{})
        valueDict[int(i)]['Order'] = int(j)
        valueDict[int(i)]['fuelType'] = k
        valueDict[int(i)]['WPS'] = int(l)
        valueDict[int(i)]['SPS'] = int(m)
        valueDict[int(i)]['CCS'] = int(n)
        valueDict[int(i)]['CAP'] = float(o)
        valueDict[int(i)]['Speed'] = float(p)
    return valueDict

def unitCostFuelFunc(filename,fuelName,year):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    #print("unitCostFuel")
    #display(csv_input)
    #print("\n")
    measureYear = np.array(csv_input['Year'],dtype='float64')
    measureHFO = np.array(csv_input['HFO'],dtype='float64')
    measure = np.array(csv_input[fuelName],dtype='float64')
    fittedHFO = interpolate.interp1d(measureYear, measureHFO)
    fitted = interpolate.interp1d(measureYear, measure)
    if year >= 2020:
        interp = fitted(year)
        interpHFO = fittedHFO(year)
    else:
        interp = measure[0]
        interpHFO = measureHFO[0]
    return interp, interpHFO

def rShipBasicFunc(filename,fuelName,CAPcnt):
    csv_input = pd.read_csv(filepath_or_buffer=filename, encoding="utf_8", sep=",")
    #print("CeqLHV")
    #display(csv_input)
    #print("\n")
    fuelType = csv_input['Fuel type']
    rShipBasic = csv_input['rShipBasic']
    fuelDict = {}
    for i, j in zip(fuelType, rShipBasic):
        fuelDict[i] = float(j)
    return fuelDict[fuelName]

def wDWTFunc(kDWT1,CAPcnt,kDWT2):
    wDWT = kDWT1*CAPcnt+kDWT2
    return wDWT

def wFLDFunc(kFLD1,wDWT,kFLD2):
    wFLD = kFLD1*wDWT+kFLD2
    return wFLD

def dFunc(Dyear,Hday,v,Rrun):
    d = Dyear*Hday*v*Rrun
    return d

def fShipFunc(kShip1,kShip2,wDWT,wFLD,rocc,CNM2km,v,d,rWPS,windPr,CeqLHV):
    fShipORG = (kShip1/1000)*(wFLD-(1-kShip2*rocc)*wDWT)*(wFLD**(-1/3))*((CNM2km*v)**2)*CNM2km*d
    if windPr:
        fShipORG = fShipORG*(1-rWPS)
    else:
        fShipORG = fShipORG
    fShip = CeqLHV*fShipORG
    return fShipORG, fShip

def fAuxFunc(Dyear,Hday,Rrun,kAux1,kAux2,wDWT,rSPS,solar):
    fAuxORG = Dyear*Hday*Rrun*(kAux1+kAux2*wDWT)/1000
    if solar:
        fAux = fAuxORG*(1-rSPS)
    else:
        fAux = fAuxORG
    return fAuxORG, fAux

def gFunc(Cco2,fShip,Cco2DF,fAux,rCCS,CCS):
    gORG = Cco2*fShip+Cco2DF*fAux
    if CCS:
        g = gORG*(1-rCCS)
    else:
        g = gORG
    return gORG, g

def ctaPerRoccFunc(CAPcnt,d):
    ctaPerRocc = CAPcnt*d
    return ctaPerRocc

def ctaFunc(CAPcnt,rocc,d):
    cta = CAPcnt*rocc*d
    return cta

def costFuelShipFunc(unitCostFuelHFO, unitCostFuel, fShipORG, fShip):
#def costFuelShipFunc(unitCostFuelHFO, unitCostFuel, fShipORG, fShip, currentYear, fuelName):
    costFuelShipORG = unitCostFuelHFO*fShipORG
    costFuelShip = unitCostFuel*fShip
    #print('unitCostFuelHFO: ', unitCostFuelHFO, 'fShipORG: ', fShipORG, 'unitCostFuel: ', unitCostFuel, 'fShip: ', fShip, )
    dcostFuelShip = costFuelShip - costFuelShipORG
    #print(currentYear, ', ', fuelName, ', uniCostFuelHFO: ', unitCostFuelHFO, ', uniCostFuelHFO: ', unitCostFuel, 'costFuelShipOrg: ', costFuelShipORG, ', costFuelShip: ', costFuelShip)
    return costFuelShipORG, costFuelShip, dcostFuelShip

def costFuelAuxFunc(unitCostDF, fAuxORG, fAux):
    costFuelAuxORG = unitCostDF*fAuxORG
    costFuelAux = unitCostDF*fAux
    #print('costFuelAuxORG: ', costFuelAuxORG, ', costFuelAux: ', costFuelAux)
    dcostFuelAux = costFuelAux - costFuelAuxORG
    return costFuelAuxORG, costFuelAux, dcostFuelAux

def costFuelAllFunc(costFuelShip, costFuelAux, dcostFuelShip, dcostFuelAux):
    costFuelAll = costFuelShip+costFuelAux
    dcostFuelAll = dcostFuelShip+dcostFuelAux
    #print('costFuelAll: ', costFuelAll, ', dcostFuelAll: ', dcostFuelAll, ', dcostFuelShip: ', dcostFuelShip, ', dcostFuelAux: ', dcostFuelAux)
    return costFuelAll, dcostFuelAll

def costShipFunc(kShipBasic1, CAPcnt, kShipBasic2, rShipBasic, dcostWPS, dcostSPS, dcostCCS, flagWPS, flagSPS, flagCCS):
    costShipBasicHFO = kShipBasic1 * CAPcnt + kShipBasic2
    costShipBasic = rShipBasic * costShipBasicHFO
    cAdditionalEquipment = 1
    if flagWPS:
        cAdditionalEquipment = cAdditionalEquipment + dcostWPS
    if flagSPS:
        cAdditionalEquipment = cAdditionalEquipment + dcostSPS
    if flagCCS:
        cAdditionalEquipment = cAdditionalEquipment + dcostCCS
    #costShipAll = (1+dcostWPS+dcostSPS+dcostCCS) * costShipBasic
    costShipAll = cAdditionalEquipment * costShipBasic
    #print('costShipBasicHFO: ', costShipBasicHFO, ', costShipBasic: ', costShipBasic, ', costShipAll: ', costShipAll)
    #print('dcostWPS: ', dcostWPS, ', dcostSPS: ', dcostSPS, ', dcostCCS: ', dcostCCS)
    return costShipBasicHFO, costShipBasic, costShipAll

def additionalShippingFeeFunc(tOp, tOpSch, dcostFuelAll, costShipAll, costShipBasicHFO):
#def additionalShippingFeeFunc(tOp, tOpSch, dcostFuelAll, costShipAll, costShipBasicHFO, currentYear, fuelName):
    if tOp <= tOpSch:
        dcostShipping = dcostFuelAll + (costShipAll-costShipBasicHFO)/tOpSch
        #print('dcostFuelAll: ', dcostFuelAll, ', dcostShip: ', (costShipAll-costShipBasicHFO)/tOpSch, ', dcostShipping: ', dcostShipping)
        #print('1, year: ', currentYear, ', fuelName: ', fuelName, 'dcostFuelAll: ', dcostFuelAll, ', dcostShip: ', (costShipAll-costShipBasicHFO)/tOpSch, ', dcostShipping: ', dcostShipping)
    else:
        dcostShipping = dcostFuelAll
        #print('dcostFuelAll: ', dcostFuelAll, ', dcostShipping: ', dcostShipping)
        #print('2, year: ', currentYear, ', fuelName: ', fuelName, 'dCostShipping; ', dcostShipping)
    return dcostShipping

def demandScenarioFunc(year,kDem1,kDem2,kDem3,kDem4):
    Di = (kDem1*year**2 + kDem2*year + kDem3)*1000000000/kDem4
    return Di

def orderShipFunc(fleetAll,fuelName,WPS,SPS,CCS,CAPcnt,tOpSch,tbid,iniT,currentYear,parameterFile2,parameterFile3,parameterFile5):
    NumFleet = len(fleetAll)-2
    fleetAll.setdefault(NumFleet,{})
    fleetAll[NumFleet]['fuelName'] = fuelName
    fleetAll[NumFleet]['WPS'] = WPS
    fleetAll[NumFleet]['SPS'] = SPS
    fleetAll[NumFleet]['CCS'] = CCS
    fleetAll[NumFleet]['CAPcnt'] = float(CAPcnt)

    fleetAll[NumFleet]['CeqLHV'] = CeqLHVFunc(parameterFile2,fleetAll[NumFleet]['fuelName'])
    fleetAll[NumFleet]['Cco2'] = Cco2Func(parameterFile3,fleetAll[NumFleet]['fuelName'])
    fleetAll[NumFleet]['rShipBasic'] = rShipBasicFunc(parameterFile5,fleetAll[NumFleet]['fuelName'],fleetAll[NumFleet]['CAPcnt'])
    fleetAll[NumFleet]['delivery'] = currentYear+tbid
    fleetAll[NumFleet]['tOp'] = iniT
    fleetAll[NumFleet]['v'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['rocc'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['wDWT'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['wFLD'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['d'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['fShipORG'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['fAuxORG'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['gORG'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['costFuelShipORG'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['costFuelShip'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['dcostFuelShip'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['costFuelAuxORG'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['costFuelAux'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['dcostFuelAux'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['dcostFuelAll'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['fShip'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['fAux'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['g'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['cta'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['costFuelAll'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['costShipBasicHFO'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['costShipBasic'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['costShipAll'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['dcostShipping'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['gTilde'] = np.zeros(tOpSch)
    fleetAll[NumFleet]['dcostShippingTilde'] = np.zeros(tOpSch)
    return fleetAll

#def yearlyOperationFunc(fleetAll,startYear,elapsedYear,NShipFleet,Alpha,tOpSch,v,valueDict,parameterFile4):　# tkinterによるInput用
def yearlyOperationFunc(fleetAll,startYear,elapsedYear,NShipFleet,Alpha,tOpSch,v,valueDict,parameterFile4):
    NumFleet = len(fleetAll)-2

    j = 0
    ctaPerRocc = 0
    currentYear = startYear+elapsedYear
    for i in range(1,NumFleet):
        if fleetAll[i]['delivery'] <= currentYear and fleetAll[i]['tOp'] < tOpSch:
            tOpTemp = fleetAll[i]['tOp']
            #unitCostFuel, unitCostFuelHFO = unitCostFuelFunc(parameterFile4,fleetAll[i]['fuelName'],currentYear)
            #fleetAll[i]['v'][tOpTemp] = v[j].get() # tkinterによるInput用
            fleetAll[i]['v'][tOpTemp] = v
            fleetAll[i]['wDWT'][tOpTemp] = wDWTFunc(valueDict["kDWT1"],fleetAll[i]['CAPcnt'],valueDict["kDWT2"])
            fleetAll[i]['wFLD'][tOpTemp] = wFLDFunc(valueDict["kFLD1"],fleetAll[i]['wDWT'][tOpTemp],valueDict["kFLD2"])
            fleetAll[i]['d'][tOpTemp] = dFunc(valueDict["Dyear"],valueDict["Hday"],fleetAll[i]['v'][tOpTemp],valueDict["Rrun"])
            ctaPerRocc += NShipFleet * ctaPerRoccFunc(fleetAll[i]['CAPcnt'],fleetAll[i]['d'][tOpTemp])
            j += 1

    numFleetAlive = 0
    for i in range(1,NumFleet):
        if fleetAll[i]['delivery'] <= currentYear and fleetAll[i]['tOp'] < tOpSch:
            tOpTemp = fleetAll[i]['tOp']
            Di = demandScenarioFunc(currentYear,valueDict["kDem1"],valueDict["kDem2"],valueDict["kDem3"],valueDict["kDem4"])
            if Di / ctaPerRocc <= 1.0 and Di / ctaPerRocc > 0.0:
                fleetAll[i]['rocc'][tOpTemp] = Di / ctaPerRocc
            else:
                print('ERROR: rocc should be 0.0 < rocc <= 1.0 but now',Di/ctaPerRocc,' in ',currentYear,'.')
                sys.exit()
            fleetAll[i]['cta'][tOpTemp] = ctaFunc(fleetAll[i]['CAPcnt'],fleetAll[i]['rocc'][tOpTemp],fleetAll[i]['d'][tOpTemp])
            fleetAll[i]['fShipORG'][tOpTemp], fleetAll[i]['fShip'][tOpTemp] = fShipFunc(valueDict["kShip1"],valueDict["kShip2"],fleetAll[i]['wDWT'][tOpTemp],fleetAll[i]['wFLD'][tOpTemp],fleetAll[i]['rocc'][tOpTemp],valueDict["CNM2km"],fleetAll[i]['v'][tOpTemp],fleetAll[i]['d'][tOpTemp],valueDict["rWPS"],fleetAll[i]['WPS'],fleetAll[i]['CeqLHV'])
            fleetAll[i]['fAuxORG'][tOpTemp], fleetAll[i]['fAux'][tOpTemp] = fAuxFunc(valueDict["Dyear"],valueDict["Hday"],valueDict["Rrun"],valueDict["kAux1"],valueDict["kAux2"],fleetAll[i]['wDWT'][tOpTemp],valueDict["rSPS"],fleetAll[i]['SPS'])
            fleetAll[i]['gORG'][tOpTemp], fleetAll[i]['g'][tOpTemp] = gFunc(fleetAll[i]['Cco2'],fleetAll[i]['fShip'][tOpTemp],valueDict["Cco2DF"],fleetAll[i]['fAux'][tOpTemp],valueDict["rCCS"],fleetAll[i]['CCS'])     
            unitCostFuel, unitCostFuelHFO = unitCostFuelFunc(parameterFile4,fleetAll[i]['fuelName'],currentYear)
            print(currentYear, ', ', fleetAll[i]['fuelName'], ', unitCostFuelHFO: ', unitCostFuelHFO, ', unitCostFuel: ', unitCostFuel)
            fleetAll[i]['costFuelShipORG'][tOpTemp], fleetAll[i]['costFuelShip'][tOpTemp], fleetAll[i]['dcostFuelShip'][tOpTemp] = costFuelShipFunc(unitCostFuelHFO, unitCostFuel, fleetAll[i]['fShipORG'][tOpTemp], fleetAll[i]['fShip'][tOpTemp])
            #fleetAll[i]['costFuelShipORG'][tOpTemp], fleetAll[i]['costFuelShip'][tOpTemp], fleetAll[i]['dcostFuelShip'][tOpTemp] = costFuelShipFunc(unitCostFuelHFO, unitCostFuel, fleetAll[i]['fShipORG'][tOpTemp], fleetAll[i]['fShip'][tOpTemp], currentYear, fleetAll[i]['fuelName'])
            fleetAll[i]['costFuelAuxORG'][tOpTemp], fleetAll[i]['costFuelAux'][tOpTemp], fleetAll[i]['dcostFuelAux'][tOpTemp] = costFuelAuxFunc(valueDict["unitCostDF"], fleetAll[i]['fAuxORG'][tOpTemp], fleetAll[i]['fAux'][tOpTemp])
            fleetAll[i]['costFuelAll'][tOpTemp], fleetAll[i]['dcostFuelAll'][tOpTemp] = costFuelAllFunc(fleetAll[i]['costFuelShip'][tOpTemp], fleetAll[i]['costFuelAux'][tOpTemp], fleetAll[i]['dcostFuelShip'][tOpTemp], fleetAll[i]['dcostFuelAux'][tOpTemp])
            #print('costFuelAll: ', fleetAll[i]['costFuelAll'][tOpTemp], ', dcostFuelAll: ', fleetAll[i]['dcostFuelAll'][tOpTemp])
            fleetAll[i]['costShipBasicHFO'][tOpTemp], fleetAll[i]['costShipBasic'][tOpTemp], fleetAll[i]['costShipAll'][tOpTemp] = costShipFunc(valueDict["kShipBasic1"], fleetAll[i]["CAPcnt"], valueDict["kShipBasic2"], fleetAll[i]['rShipBasic'], valueDict["dcostWPS"], valueDict["dcostSPS"], valueDict["dcostCCS"], fleetAll[i]['WPS'], fleetAll[i]['SPS'], fleetAll[i]['CCS'])
            fleetAll[i]['dcostShipping'][tOpTemp] = additionalShippingFeeFunc(tOpTemp, tOpSch, fleetAll[i]['dcostFuelAll'][tOpTemp], fleetAll[i]['costShipAll'][tOpTemp], fleetAll[i]['costShipBasicHFO'][tOpTemp])
            #fleetAll[i]['dcostShipping'][tOpTemp] = additionalShippingFeeFunc(tOpTemp, tOpSch, fleetAll[i]['dcostFuelAll'][tOpTemp], fleetAll[i]['costShipAll'][tOpTemp], fleetAll[i]['costShipBasicHFO'][tOpTemp], currentYear, fleetAll[i]['fuelName'])
            fleetAll[i]['gTilde'][tOpTemp] = fleetAll[i]['g'][tOpTemp] / fleetAll[i]['cta'][tOpTemp]
            fleetAll[i]['dcostShippingTilde'][tOpTemp] = fleetAll[i]['dcostShipping'][tOpTemp] / fleetAll[i]['cta'][tOpTemp]
            #fleetAll['output']['gTilde'][elapsedYear] += NShipFleet * fleetAll[i]['gTilde'][tOpTemp]
            fleetAll['output']['g'][elapsedYear] += NShipFleet * fleetAll[i]['g'][tOpTemp]
            fleetAll['output']['cta'][elapsedYear] += NShipFleet * fleetAll[i]['cta'][tOpTemp]
            fleetAll['output']['rocc'][elapsedYear] = fleetAll[i]['rocc'][tOpTemp]
            #print('year: ', currentYear, ', i: ', i, ', rocc: ', fleetAll[i]['rocc'][tOpTemp], ', # of fleet: ', NumFleet)
            fleetAll['output']['ctaPerRocc'][elapsedYear] = ctaPerRocc
            fleetAll['output']['dcostShipping'][elapsedYear] += NShipFleet * fleetAll[i]['dcostShipping'][tOpTemp]
            #print('year: ', currentYear, ', fuel: ', fleetAll[i]['fuelName'], 'dCostShipping: ', fleetAll[i]['dcostFuelAll'][tOpTemp])
            fleetAll['output']['dcostShippingTilde'][elapsedYear] += NShipFleet * fleetAll[i]['dcostShippingTilde'][tOpTemp]
            numFleetAlive += 1
    
    #fleetAll['output']['rocc'][elapsedYear] = fleetAll[NumFleet]['rocc'][tOpTemp]
    fleetAll['output']['gTilde'][elapsedYear] = fleetAll['output']['g'][elapsedYear] / fleetAll['output']['cta'][elapsedYear]
    
    Si = 0
    for i in range(1,NumFleet):
        if fleetAll[i]['delivery'] <= currentYear:
            tOpTemp = fleetAll[i]['tOp']
            if tOpTemp < tOpSch:
                Si += fleetAll[i]['dcostShippingTilde'][tOpTemp] - Alpha * fleetAll[i]['gTilde'][tOpTemp]
            fleetAll[i]['tOp'] += 1
    if numFleetAlive > 0:
        fleetAll['S'][elapsedYear] = Si / numFleetAlive
    else:
        fleetAll['S'][elapsedYear] = 0

    fleetAll['year'][elapsedYear] = currentYear
    return fleetAll

def buttonCommandOrder(fleetAll,v1,v2,v3,v4,v5,tOpSch,tbid,iniT,currentYear,parameterFile2,parameterFile3,parameterFile5):
    def inner():
        fleetTemp = fleetAll
        fleetTemp = orderShipFunc(fleetTemp,v1.get(),v2.get(),v3.get(),v4.get(),v5.get(),tOpSch,tbid,iniT,currentYear,parameterFile2,parameterFile3,parameterFile5)
        return fleetTemp
    return inner

def buttonCommandSkip(root):
    def inner():
        root.quit()
        root.destroy()
    return inner

def orderShipInputFunc(fleetAll,tOpSch,tbid,iniT,currentYear,parameterFile2,parameterFile3,parameterFile5):
    root = Tk()
    root.title('Order Fleet')
    root.geometry('500x300')

    # Frame
    frame = ttk.Frame(root, padding=20)
    frame.pack()

    # Combobox fuelName
    v1 = StringVar()
    fuel = ['HFO', 'LNG', 'NH3', 'H2']
    cb1 = ttk.Combobox(frame, textvariable=v1, values=fuel, width=20)
    cb1.set(fuel[0])

    # Checkbutton WPS
    v2 = StringVar()
    v2.set('0') # 初期化
    cb2 = ttk.Checkbutton(frame, padding=(10), text='WPS: Wind Propulsion System', variable=v2)

    # Checkbutton SPS
    v3 = StringVar()
    v3.set('0') # 初期化
    cb3 = ttk.Checkbutton(frame, padding=(10), text='SPS: Solar Propulsion System', variable=v3)

    # Checkbutton CCS
    v4 = StringVar()
    v4.set('0') # 初期化
    cb4 = ttk.Checkbutton(frame, padding=(10), text='CCS: Carbon Capture and Storage', variable=v4)

    # Scale
    v5 = IntVar()
    v5.set(20000)
    sc = Scale(frame,orient="horizontal",length=200,variable=v5,from_=0,to=50000,label='CAPcnt [TEU]')

    # Button
    button1 = ttk.Button(frame, text='Order', command=buttonCommandOrder(fleetAll,v1,v2,v3,v4,v5,tOpSch,tbid,iniT,currentYear,parameterFile2,parameterFile3,parameterFile5))
    button2 = ttk.Button(frame, text='Skip', command=buttonCommandSkip(root))

    # Layout
    cb1.grid(row=0, column=0)
    cb2.grid(row=1, column=0)
    cb3.grid(row=2, column=0)
    cb4.grid(row=3, column=0)
    sc.grid(row=4, column=0)
    button1.grid(row=5, column=0, columnspan=2)
    button2.grid(row=5, column=1, columnspan=2)

    root.deiconify()
    root.mainloop()

    return fleetAll

def buttonCommandSpeed(fleetAll, startYear,elapsedYear,NShipFleet,Alpha,tOpSch,v,valueDict,parameterFile4,root):
    def inner():
        fleetTemp = fleetAll
        fleetTemp = yearlyOperationFunc(fleetTemp,startYear,elapsedYear,NShipFleet,Alpha,tOpSch,v,valueDict,parameterFile4)
        root.quit()
        root.destroy()
        return fleetTemp
    return inner

def yearlyOperationInputFunc(fleetAll,startYear,elapsedYear,NShipFleet,Alpha,tOpSch,valueDict,parameterFile4):
    NumFleet = len(fleetAll)-2
    currentYear = startYear+elapsedYear

    root = Tk()
    root.title('Yealy Operation in %s: Input Service Speed [kt]' % currentYear)
    root.geometry('500x300')

    # Frame
    frame = ttk.Frame(root, padding=20)
    frame.pack()

    # Label
    label = Label(frame,text="Input Service Speed [kt].",justify=LEFT)
    label.grid(row=0, column=0)

    # Scale
    v = []
    sc = []
    j = 0
    for i in range(1,NumFleet):
        if fleetAll[i]['delivery'] <= currentYear and fleetAll[i]['tOp'] < tOpSch:
            v.append(DoubleVar(value=20))
            FleetName = 'Fleet ' + str(i)
            sc.append(Scale(frame,orient="horizontal",length=200,variable=v[j],from_=0,to=50,label=FleetName))
            sc[j].grid(row=j+1, column=0)
            j += 1

    # Button
    button = ttk.Button(frame, text='Complete', command=buttonCommandSpeed(fleetAll,startYear,elapsedYear,NShipFleet,Alpha,tOpSch,v,valueDict,parameterFile4,root))

    # Layout
    button.grid(row=i+1, column=0, columnspan=2)

    root.mainloop()

    return fleetAll
    
def buttonCommandOutput(root):
    def inner():
        root.quit()
        root.destroy()
    return inner

def outputGUIFunc(fleetAll,startYear,elapsedYear,tOpSch):
    #fig = plt.figure()
    fig = Figure(figsize=(5, 4), dpi=100)
    ax1 = fig.add_subplot(121)
    ax1.plot(fleetAll['year'][0:elapsedYear],fleetAll['S'][0:elapsedYear])

    ax2 = fig.add_subplot(122)
    NumFleet = len(fleetAll)-2
    currentYear = startYear+elapsedYear
    for i in range(1,NumFleet):
        if fleetAll[i]['delivery'] <= currentYear and fleetAll[i]['tOp'] < tOpSch:
            print(fleetAll['year'][0:elapsedYear], fleetAll[i]['g'][0:elapsedYear])
            if i == 1:
                ax2.bar(fleetAll['year'][0:elapsedYear], fleetAll[i]['g'][0:elapsedYear])
            else:
                ax2.bar(fleetAll['year'][0:elapsedYear], fleetAll[i]['g'][0:elapsedYear], bottom=fleetAll[i-1]['g'][0:elapsedYear])

    # Tkinter Class
    root = Tk()

    # Frame
    frame = ttk.Frame(root, padding=20)
    frame.pack()

    # Canvas
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().grid(row=0, column=0)

    toolbar = NavigationToolbar2Tk(canvas, root)
    toolbar.update()
    canvas.get_tk_widget().grid(row=0, column=0)

    def on_key_press(event):
        print("you pressed {}".format(event.key))
        key_press_handler(event, canvas, toolbar)

    def _quit():
        root.quit()     # stops mainloop
        root.destroy()  # this is necessary on Windows to prevent

    canvas.mpl_connect("key_press_event", on_key_press)

    # Button
    button = Button(master=frame, text="Resume Operation", command=_quit)
    button.grid(row=1, column=0)

    # root
    mainloop()

def outputFunc(fleetAll,startYear,elapsedYear,lastYear,tOpSch,decisionListName):
    fig, ax = plt.subplots(3, 2, figsize=(10.0, 10.0))
    plt.subplots_adjust(wspace=0.4, hspace=0.6)

    gPlot = fleetAll['output']['g'][:elapsedYear+1]/1000000
    ax[0,0].plot(fleetAll['year'][:elapsedYear+1],fleetAll['output']['g'][:elapsedYear+1]/1000000)
    ax[0,0].set_title("g")
    ax[0,0].set_xlabel('Year')
    ax[0,0].set_ylabel('Millions ton')
    ax[0,0].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax[0,0].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))

    gTildePlot = fleetAll['output']['gTilde'][:elapsedYear+1]*1000000
    ax[0,1].plot(fleetAll['year'][:elapsedYear+1],fleetAll['output']['gTilde'][:elapsedYear+1]*1000000)
    ax[0,1].set_title("g / cta")
    ax[0,1].set_xlabel('Year')
    ax[0,1].set_ylabel('g / (TEU $\cdot$ NM)')
    #ax[0,1].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax[0,1].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))

    roccPlot = fleetAll['output']['rocc'][:elapsedYear+1]
    ax[1,0].plot(fleetAll['year'][:elapsedYear+1],fleetAll['output']['rocc'][:elapsedYear+1])
    ax[1,0].set_title("r_occ")
    ax[1,0].set_xlabel('Year')
    ax[1,0].set_ylabel('r_occ')
    ax[1,0].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax[1,0].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    
    ctaPerRoccPlot = fleetAll['output']['ctaPerRocc'][:elapsedYear+1]
    ax[1,1].plot(fleetAll['year'][:elapsedYear+1],fleetAll['output']['ctaPerRocc'][:elapsedYear+1])
    ax[1,1].set_title("ctaPerRocc")
    ax[1,1].set_xlabel('Year')
    ax[1,1].set_ylabel('ctaPerRocc')
    ax[1,1].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax[1,1].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    
    SPlot = fleetAll['S'][:elapsedYear+1]
    ax[2,0].plot(fleetAll['year'][:elapsedYear+1],fleetAll['S'][:elapsedYear+1])
    ax[2,0].set_title(r"$ ( \Delta C_{shipping} - \alpha g) \ / \ cta$")
    ax[2,0].set_xlabel('Year')
    ax[2,0].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax[2,0].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    #ax[0].set_ylabel('Year')
    
    dcostShippingPlot = fleetAll['output']['dcostShipping'][:elapsedYear+1]
    ax[2,1].plot(fleetAll['year'][:elapsedYear+1],fleetAll['output']['dcostShipping'][:elapsedYear+1])
    ax[2,1].set_title("$\Delta C_{shipping}$")
    ax[2,1].set_xlabel('Year')
    ax[2,1].set_ylabel('\$')
    ax[2,1].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax[2,1].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))

    dcostShippingTildePlot = fleetAll['output']['dcostShippingTilde'][:elapsedYear+1]
#    ax[2,1].plot(fleetAll['year'][:elapsedYear+1],fleetAll['output']['dcostShippingTilde'][:elapsedYear+1])
#    ax[2,1].set_title("$\Delta C_{shipping} \ / \ cta$")
#    ax[2,1].set_xlabel('Year')
#    ax[2,1].set_ylabel('\$ / (TEU $\cdot$ NM)')
#    ax[2,1].yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
#    ax[2,1].ticklabel_format(style="sci",  axis="y",scilimits=(0,0))
    
    ctaPlot = fleetAll['output']['cta'][:elapsedYear+1]
    
    if os.name == 'nt':
        plt.show()
    elif os.name == 'posix':
        plt.savefig(decisionListName+".jpg")
        np.savetxt(decisionListName+'_S.csv',SPlot)
        np.savetxt(decisionListName+'_gTilde.csv',gTildePlot)
        np.savetxt(decisionListName+'_g.csv',gPlot)
        np.savetxt(decisionListName+'_dcostShippingTilde.csv',dcostShippingTildePlot)
        np.savetxt(decisionListName+'_cta.csv',ctaPlot)
        np.savetxt(decisionListName+'_rocc.csv',roccPlot)
        np.savetxt(decisionListName+'_ctaPerRocc.csv',ctaPerRoccPlot)
        np.savetxt(decisionListName+'_dcostShipping.csv',dcostShippingPlot)
