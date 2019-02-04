# Bibliotheken importieren

from lib_oled96 import ssd1306
from smbus import SMBus
from PIL import ImageFont
from PIL import Image
import time
from datetime import datetime
import RPi.GPIO as GPIO
import os
import sys
import socket


GPIO.setmode(GPIO.BCM) # ansprechen der GPIO über GPIO Nummer statt Pinnummer
GPIO.setwarnings(False)


# Variablen und Systemsettings

i2cbus = SMBus(1)            #1 = Raspberry Pi > 1
oled = ssd1306(i2cbus)
draw = oled.canvas

oled.cls()

global k, x, state, USER_Interrupt, interrupted_CTRL1, interrupted_CTRL2, interrupted_ErrorLine, interrupted_Emit1, interrupted_Emit2, interrupted_Gate1, interrupted_Gate2, interrupted_Temp1, interrupted_Temp2

k = 0 # 3 = ein 0 = Aus
x = 0
state = 0
USER_Interrupt = 0
interrupted_ErrorLine = 0
interrupted_Emit1 = 0
interrupted_Emit2 = 0
interrupted_Gate1 = 0
interrupted_Gate2 = 0
interrupted_CTRL1 = 0
interrupted_CTRL2 = 0
interrupted_Temp1 = 0
interrupted_Temp2 = 0

#Bewertungsvariablen (Global)

# ............................................
FreeSans8 = ImageFont.truetype('FreeSans.ttf', 8)
FreeSans10 = ImageFont.truetype('FreeSans.ttf', 10)
FreeSans12 = ImageFont.truetype('FreeSans.ttf', 12)
FreeSans14 = ImageFont.truetype('FreeSans.ttf', 14)
FreeSans16 = ImageFont.truetype('FreeSans.ttf', 16)
FreeSans18 = ImageFont.truetype('FreeSans.ttf', 18)
FreeSans20 = ImageFont.truetype('FreeSans.ttf', 20)
FreeSans24 = ImageFont.truetype('FreeSans.ttf', 24)
FreeSans28 = ImageFont.truetype('FreeSans.ttf', 28)
FreeSans30 = ImageFont.truetype('FreeSans.ttf', 30)

# Setup der Ein- und Ausgänge des GPIO Registers (40pin-Steckverbinder)
# Eingänge

Temp1_In = 10     # Temperatursensorsteckplatz T1 Eingang Nur bei ProWind
Temp2_In = 20     # Temperatursensorsteckplatz T2 Eingang Nur bei Prowind
Status_PW_T1 = 13        # Statuseingang T1
Status_PW_T2 = 26        # Statuseingang T2
MessCol_1 = 18      # Statuseingang Collector C1
MessCol_2 = 14      # Statuseingang Collector C2
MessEmit1 = 25      # Statuseingang Emitter E1
MessEmit2 = 15      # Statuseingang Emitter E2
MessGate1 = 12      # Statuseingang G1
MessGate2 = 7       # Statuseingang G2
ErrorLine = 4	     # MD2000 Fehlersignal
ProWErk = 21        # ProWind-Erkennung
Shutdown_Button = 23   # SHUTDOWN-EINGANG - Taster "Shutdown" 
Start_Button = 19  # Eingang START TEST-Signal (High) --> t>5 IP-Adresse auslesen / t>7s GPIO TEST

# Steuerleitungen:

Temp1_CTRL = 9        # Temperatursensorsteckplatz T1 Ausgang Nur bei Prowind
Temp2_CTRL= 16       # Temperatursensorsteckplatz T2 Ausgang Nur bei Prowind
CTRL_TOP = 11       # CTRL_TOP - Ausgang (Bei MD2000 UND ProWind Pin 11)
CTRL_BOT_PW = 8     # CTRL_BOTTOM  PROWIND - Ausgang

#
NOK_LED = 27       	# Error-LED
OK_LED = 22         # STATUS-LED -Ausgabe ob Test OK oder NOK

GPIO.setup(Temp1_In, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(Temp2_In, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(Status_PW_T1, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(Status_PW_T2, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(MessCol_1, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(MessCol_2, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(MessEmit1, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(MessEmit2, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(MessGate1, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(MessGate2, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

GPIO.setup(ErrorLine, GPIO.IN, pull_up_down = GPIO.PUD_DOWN) # entspricht analog CTRL_TOP
GPIO.setup(ProWErk, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
GPIO.setup(Shutdown_Button, GPIO.IN, pull_up_down = GPIO.PUD_DOWN) 
GPIO.setup(Start_Button, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

# Signalausgänge

GPIO.setup(CTRL_TOP, GPIO.OUT) # PWM-gesteuerter Pin - MD2000 & ProWind
GPIO.setup(CTRL_BOT_PW, GPIO.OUT) # Nur ProWind
GPIO.setup(Temp1_CTRL, GPIO.OUT)
GPIO.setup(Temp2_CTRL, GPIO.OUT)
GPIO.setup(NOK_LED, GPIO.OUT)
GPIO.setup(OK_LED, GPIO.OUT)


# Welcome
oled.cls()
draw.rectangle((0, 0, 127, 63), outline=1, fill=0)
draw.bitmap((0, 0), Image.open('/home/pi/lib_oled96/ZEAG.bmp'), fill=1)
oled.display()
time.sleep(4)



# Ausführen und Aufruf des Interrupts
def interrupt_by_user(Shutdown_Button):
   #global USER_interrupt
   USER_interrupt =1
   print ("USER-Interrupt aktiv \n")
   GPIO.remove_event_detect(Shutdown_Button)

def interrupt_Col1(MessCol_1):
   #global interrupted_CTRL_TOP
   interrupted_CTRL_TOP = 1
   GPIO.remove_event_detect(MessCol_1)

def interrupt_Col2(MessCol_2):
   #global interrupted_ErrorLine
   interrupted_ErrorLine = 1
   GPIO.remove_event_detect(MessCol_2)
	
def interrupt_Emit1(MessEmit1):
   #global interrupted_Emit1
   interrupted_Emit1 = 1
   GPIO.remove_event_detect(MessEmit1)

def interrupt_Emit2(MessEmit2):
   #global interrupted_Emit2
   interrupted_Emit2 = 1
   GPIO.remove_event_detect(MessEmit2)

def interrupt_Gate1(MessGate1):
   #global interrupted_Gate1
   interrupted_Gate1 = 1
   GPIO.remove_event_detect(MessGate1)

def interrupt_Gate2(MessGate2):
   #global interrupted_Gate2
   interrupted_Gate2 = 1
   GPIO.remove_event_detect(MessGate2)
	
def interrupt_Temp1(Temp1_In):
   #global interrupted_Temp1
   interrupted_Temp1 = 1
   GPIO.remove_event_detect(Temp1_In)

def interrupt_Temp2(Temp2_In):
   #global interrupted_Temp2
   interrupted_Temp2 = 1
   GPIO.remove_event_detect(Temp2_In)
 

# aktiviere Kanäle:

GPIO.add_event_detect(Shutdown_Button, GPIO.RISING, callback = interrupt_by_user, bouncetime = 1000)
GPIO.add_event_detect(MessCol_1, GPIO.RISING, callback = interrupt_Col1, bouncetime = 1000)
GPIO.add_event_detect(MessCol_2, GPIO.RISING, callback = interrupt_Col2, bouncetime = 1000)
GPIO.add_event_detect(MessEmit1, GPIO.RISING, callback = interrupt_Emit1, bouncetime = 1000)
GPIO.add_event_detect(MessEmit2, GPIO.RISING, callback = interrupt_Emit2, bouncetime = 1000)
GPIO.add_event_detect(MessGate1, GPIO.RISING, callback = interrupt_Gate1, bouncetime = 1000)
GPIO.add_event_detect(MessGate2, GPIO.RISING, callback = interrupt_Gate2, bouncetime = 1000)
GPIO.add_event_detect(Temp1_In, GPIO.RISING, callback = interrupt_Temp1, bouncetime = 1000)
GPIO.add_event_detect(Temp2_In, GPIO.RISING, callback = interrupt_Temp2, bouncetime = 1000)

GPIO.output(NOK_LED,0)

# DutyCycles:
global dcCTRLTOP, dcCTRLBOT
dcCTRLTOP = 50 # DutyCycle Angabe in %
dcCTRLBOT = 50
# Frequencies:
global frCTRLTOP, frCTRLBOT
frCTRLTOP = 500 # Frequenz in hz
frCTRLBOT = 500
# 
global pwmLine1, pwmLine2
pwmLine1 = GPIO.PWM(CTRL_TOP, dcCTRLTOP)
pwmLine2 = GPIO.PWM(CTRL_BOT_PW, dcCTRLBOT)

global comeback
comeback = 2

# Aufstart und Mitteilung der eigenen IP-Adresse (Analyse-Zwecke)
def getIP():
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    if(True):
        draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
        draw.text((10, 2), "IP-Adresse:", font=FreeSans12, fill=1)
        draw.text((10, 15), IP, font=FreeSans12, fill=1) # Ausgabe der eigenen IP
        oled.display()
        time.sleep(3)
        Tasterabfrage()
        
def Tasterabfrage(): # Auswahl des Betriebsmodus - Es können 3 Programme gewählt werden.
    
    oled.cls()
    GPIO.output(NOK_LED,0)
    value = 0
    while GPIO.input(Start_Button)==0:
        draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
        draw.text((10, 2), "START TEST?", font=FreeSans16, fill=1)
        draw.text((30, 20), "TASTE ", font=FreeSans20, fill=1)
        draw.text((15, 45), "DRÜCKEN", font=FreeSans20, fill=1)
        oled.display()
      
                   
    while True:
        if GPIO.input(Start_Button)==1:
           #value = 0
            value += 0.5
            draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
            draw.text((5, 15), "Sie wählen: t=" + str(value) + " s", font=FreeSans12, fill=1)
            draw.text((5, 30), "t>5s = IP-Check", font=FreeSans12, fill=1)
            draw.text((5, 45), "t>8s = E-Test", font=FreeSans12, fill=1)
            oled.display()
            time.sleep (0.5)


        # Programm 2 oder Programm 1 gewählt; wenn Wert >= 5s
        if GPIO.input(Start_Button)==0 and value >= 5 and value < 6:
            draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
            draw.text((2, 20), "''Abruf interne IP''", font=FreeSans16, fill=1)
            oled.display()
            for i in range(2):
                GPIO.output(NOK_LED,1)
                GPIO.output(OK_LED,0)
                time.sleep(.2)
                GPIO.output(NOK_LED,0)
                GPIO.output(OK_LED,1)
                time.sleep(.2)
            time.sleep(2)
            GPIO.output(NOK_LED,0)
            GPIO.output(OK_LED,0)
            getIP()
            
            return 0
        
        
# _______________Auslesen der GPIO Status _________________________________________________

        if GPIO.input(Start_Button)==0 and value >6:
            draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
            draw.text((20, 20), "E-Test", font=FreeSans20, fill=1)
            oled.display()
            time.sleep(2)
            GPIO_Test()
            
            return 0
		
        # wenn weniger 3s
        if GPIO.input(Start_Button) == 0 and value >=0.5 and  value < 5:
            time.sleep(1)
            teststart()

def GPIO_Test():
    oled.cls()
    while (1):
       GPIO.output(OK_LED,0)
       GPIO.output(NOK_LED,0)
       draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
       draw.text((2, 4), str(GPIO.input(NOK_LED)) + ": 27", font=FreeSans10, fill=1)
       draw.text((2, 16), str(GPIO.input(OK_LED)) + ": 22", font=FreeSans10, fill=1)
       draw.text((2, 28), str(GPIO.input(Temp1_In)) + ": 10", font=FreeSans10, fill=1)
       draw.text((2, 40), str(GPIO.input(Temp2_In)) + ": 20", font=FreeSans10, fill=1)
       draw.text((2, 52), str(GPIO.input(Status_PW_T1)) + ": 13", font=FreeSans10, fill=1)
       draw.text((31, 4), str(GPIO.input(Status_PW_T2)) + ": 26", font=FreeSans10, fill=1)
       draw.text((31, 16), str(GPIO.input(MessCol_1)) + ": 14", font=FreeSans10, fill=1)
       draw.text((31, 28), str(GPIO.input(MessCol_2)) + ": 18", font=FreeSans10, fill=1)
       draw.text((31, 40), str(GPIO.input(MessEmit1)) + ": 25", font=FreeSans10, fill=1)
       draw.text((31, 52), str(GPIO.input(MessEmit2)) + ": 15", font=FreeSans10, fill=1)
       draw.text((64, 4), str(GPIO.input(MessGate1)) + ": 12", font=FreeSans10, fill=1)
       draw.text((64, 16), str(GPIO.input(MessGate2)) + ": 07", font=FreeSans10, fill=1)
       draw.text((64, 28), str(GPIO.input(Shutdown_Button)) + ": 23", font=FreeSans10, fill=1)
       draw.text((64, 40), str(GPIO.input(Start_Button)) + ": 19", font=FreeSans10, fill=1)
       draw.text((64, 52), str(GPIO.input(Temp1_CTRL)) + ": 09", font=FreeSans10, fill=1)
       draw.text((100, 4), str(GPIO.input(Temp2_CTRL)) + ": 16", font=FreeSans10, fill=1)
       draw.text((100, 16), str(GPIO.input(CTRL_TOP)) + ": 11", font=FreeSans10, fill=1)
       draw.text((100, 28), str(GPIO.input(CTRL_BOT_PW)) + ": 08", font=FreeSans10, fill=1)
       draw.text((100, 40), str(GPIO.input(ErrorLine)) + ": 04", font=FreeSans10, fill=1)
       oled.display()
       GPIO.output(NOK_LED,1)
       GPIO.output(OK_LED,1)
       time.sleep(0.5)
       if GPIO.input(Shutdown_Button)==1 and GPIO.input(Start_Button) == 1:
          Tasterabfrage()

# Testbereitschaft

def teststart():
 
    oled.cls()
    GPIO.output(NOK_LED,0)
    while (1):
        
        state = GPIO.input(Start_Button)
            
        if state == 0:
           GPIO.output(OK_LED,1)
           draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0) 
           draw.text((2, 2), "Board verbunden?", font=FreeSans14, fill=1)
           draw.text((2, 25), "Test starten!", font=FreeSans20, fill=1)

            # Pfeil zum Taster
           draw.line((100, 50, 121, 61 ), fill=1)
           draw.line((110, 61, 121, 61 ), fill=1)
           draw.line((112, 51, 121, 61 ), fill=1)
           oled.display()
           GPIO.output(OK_LED,0)
           time.sleep(0.5)
           
            
        else:
           GPIO.output(OK_LED,0)
           draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)   
           draw.text((2, 2), "Nicht berühren!", font=FreeSans16, fill=1)
           draw.text((2, 25), "TESTE BOARD!", font=FreeSans16, fill=1)
           oled.display()
           time.sleep(1)
           hauptprogramm()
           


def error_error():
   while True:
      if GPIO.input(ErrorLine)==1:
         pwmLine1.stop(dcCTRLTOP)
         pwmLine2.stop(dcCTRLTOP)
         draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
         oled.display()
         draw.text((10, 20), "PLATINE ", font=FreeSans20, fill=1)
         draw.text((10, 45), "PRÜFEN", font=FreeSans20, fill=1)
         GPIO.output(NOK_LED,1)
         oled.display()      
         draw.rectangle((2, 2, 127, 22), outline=0, fill=0)
         draw.text((2, 2), "!! FEHLER !!", font=FreeSans18, fill=0)
         oled.display()
         time.sleep(0.5)
         draw.rectangle((2, 2, 127, 22), outline=0, fill=0)         
         draw.text((2, 2), "!! FEHLER !!", font=FreeSans18, fill=1)
         print ("error:" + str(GPIO.input(ErrorLine)))
         oled.display()
         time.sleep(2)
      else:
         oled.cls()
         draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
         oled.display()
         hauptprogramm()
  
# Hauptprogramm
def hauptprogramm():
   global P1,P2,P3,P4,P5,P6,P7,P8
   global comeback # Falls die Funktion durch einen Interrupt wieder aufgerufen wird
   while True:
      draw.rectangle((1, 50, 127, 63), outline=0, fill=0) 
      oled.display()
      
      if GPIO.input(ErrorLine)==0:
         GPIO.output(NOK_LED,0)
         
         if comeback == 3:
            comeback = 0
            teststart()
         comeback = 0
         #Status Reset für alle Kanäle
         P1=P2=P3=P3=P4=P5=P6=P7=P8=0
         # Teste Terminals
         GPIO.output(NOK_LED,0)
         pwmLine1.stop()
         pwmLine2.stop()
         time.sleep(0.0002)
         pwmLine1.start(dcCTRLTOP)
         pwmLine2.start(dcCTRLBOT)
         frCTRLTOP=0
         print ("Einstieg mit Frequenz gleich 0")
         
         for frCTRLTOP in range(500,5000,1000):
            if comeback == 1:
               break
            comeback = 3
            pwmLine1.ChangeFrequency(frCTRLTOP)
            pwmLine2.ChangeFrequency(frCTRLTOP)
            draw.rectangle((1, 50, 127, 63), outline=0, fill=0) 
            draw.text((2, 50), "Frequenz: " + str(round ((frCTRLTOP/1.5),0)) + " hz", font=FreeSans12, fill=1)
            print (str(round ((frCTRLTOP/1.5),0)))        
            oled.display()
            GPIO.output(NOK_LED,1)
            GPIO.output(OK_LED,1)
            time.sleep(0.5)
            GPIO.output(NOK_LED,0)
            GPIO.output(OK_LED,0)
            time.sleep(3)
            if GPIO.input(ErrorLine) ==1:
               GPIO.output(NOK_LED,1)
               pwmLine1.stop()
               pwmLine2.stop()
               error_error()
               
           
         for i in range (2):
            GPIO.output(Temp1_CTRL,1)
            GPIO.output(Temp2_CTRL,1)
            time.sleep(2)
            GPIO.output(Temp1_CTRL,0)
            GPIO.output(Temp2_CTRL,0)
            if GPIO.input(ErrorLine) ==1:
               GPIO.output(NOK_LED,1)
               pwmLine1.stop()
               pwmLine2.stop()
               error_error()

         if interrupted_CTRL1 == 1:
            P1=1
            #print ("P1 gesetzt")
         if interrupted_CTRL2 == 1:
            P2=1
            #print ("P2 gesetzt")
         if interrupted_Emit1 == 1:
            P3=1
            #print ("P3 gesetzt")
         if interrupted_Emit2 == 1:
            P4=1
            #print ("P4 gesetzt")
         if interrupted_Gate1 == 1:
            P5=1
            #print ("P5 gesetzt")
         if interrupted_Gate2 == 1:
            P6=1
            #print ("P6 gesetzt")
         if interrupted_Temp1 == 1:
            P7=1
            #print ("P7 gesetzt")
         if interrupted_Temp2 == 1:
            P8=1
            #print ("P8 gesetzt")
         pwmLine1.stop(dcCTRLTOP)
         pwmLine2.stop(dcCTRLTOP)
         Auswertung()
      if GPIO.input(ErrorLine)==1:
         error_error()
def Auswertung():
   global P1,P2,P3,P4,P5,P6,P7,P8
   draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
   draw.text((2, 30), "Auswertung", font=FreeSans16, fill=1)
   oled.display()
   time.sleep(2)
   GPIO.remove_event_detect(MessCol_1)
   
   x=0
   if x < 1: #Einmal ausführen.
      xPos1=1
      xPos2=23
      xPos3=62
      xPos4=84
      
      yPos1=2
      yPos2=18
      yPos3=34
      yPos4=50

      draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
      time.sleep(0.075)
      draw.line((1, 15, 121, 15), fill=1) # H
      oled.display()
      time.sleep(0.075)
      draw.line((1, 31, 121, 31 ), fill=1) # H
      oled.display()
      time.sleep(0.075)
      draw.line((1, 47, 121, 47), fill=1) # H
      oled.display()
      time.sleep(0.075)
      draw.line((58, 2, 58 , 62), fill=1) # V
      oled.display()
      draw.text((xPos1, yPos1), "C1: ", font=FreeSans12, fill=1)
      time.sleep(0.1)
      oled.display()
      draw.text((xPos1, yPos2), "C2: ", font=FreeSans12, fill=1)
      time.sleep(0.1)
      oled.display()
      draw.text((xPos1, yPos3), "E1: ", font=FreeSans12, fill=1)
      time.sleep(0.1)
      oled.display()
      draw.text((xPos1, yPos4), "E2: ", font=FreeSans12, fill=1)
      time.sleep(0.1)
      oled.display()
      draw.text((xPos3, yPos1), "G1: ", font=FreeSans12, fill=1)
      time.sleep(0.1)
      oled.display()
      draw.text((xPos3, yPos2), "G2: ", font=FreeSans12, fill=1)
      time.sleep(0.1)
      oled.display()
      draw.text((xPos3, yPos3), "T1: ", font=FreeSans12, fill=1)
      time.sleep(0.1)
      oled.display()
      draw.text((xPos3, yPos4), "T2: ", font=FreeSans12, fill=1)
      time.sleep(0.1)
      oled.display()
      
   warte = 1 #Angabe in Sekunden
      
   if P1 == 0:
      draw.text((xPos2, yPos1), "Fehler", font=FreeSans12, fill=1)
      oled.display()
      time.sleep(warte)

   else:
      draw.text((xPos2, yPos1), "OK", font=FreeSans12, fill=1)
      oled.display()
      time.sleep(warte)
      
   if P2 == 0:            			
      draw.text((xPos2, yPos2), "Fehler", font=FreeSans12, fill=1)
      oled.display()
      time.sleep(warte)
   else:           				
      draw.text((xPos2, yPos2), "OK", font=FreeSans12, fill=1)
      oled.display()
      time.sleep(warte)

   if P3 == 0:            				
      draw.text((xPos2, yPos3), "Fehler", font=FreeSans12, fill=1)
      oled.display()
      time.sleep(warte)
   else:        			
      draw.text((xPos2, yPos3), "OK", font=FreeSans12, fill=1)
      oled.display()
      time.sleep(warte)

   if P4 == 0:            			
      draw.text((xPos2, yPos4), "Fehler", font=FreeSans12, fill=1)
      oled.display()
      time.sleep(warte)
   else:			
      draw.text((xPos2, yPos4), "OK", font=FreeSans12, fill=1)
      oled.display()
      time.sleep(warte)

   if P5 == 0:		
      draw.text((xPos4, yPos1), "Fehler", font=FreeSans12, fill=1)
      oled.display()
      time.sleep(warte)
   else:				
      draw.text((xPos4, yPos1), "OK", font=FreeSans12, fill=1)
      oled.display()
      time.sleep(warte)
     
   if P6 == 0:		
      draw.text((xPos4, yPos2), "Fehler", font=FreeSans12, fill=1)
      oled.display()
      time.sleep(warte)
   else:			
      draw.text((xPos4, yPos2), "OK", font=FreeSans12, fill=1)
      oled.display()
      time.sleep(warte)
     
   if P7 == 0:            
      if GPIO.input(ProWErk)==0:
         draw.text((xPos4, yPos3), "ohne.A.", font=FreeSans12, fill=1)
         oled.display()
         P7=1
         time.sleep(warte)
      else:
         draw.text((xPos4, yPos3), "Fehler", font=FreeSans12, fill=1)
         oled.display()
         time.sleep(warte)
   else:           
      draw.text((xPos4, yPos3), "OK", font=FreeSans12, fill=1)
      oled.display()
      time.sleep(warte)

   if P8 == 0:            
      if GPIO.input(ProWErk)==0:
         draw.text((xPos4, yPos4), "ohne.A.", font=FreeSans12, fill=1)
         oled.display()
         P8=1
         time.sleep(warte)
   else:           			
     draw.text((xPos4, yPos4), "OK", font=FreeSans12, fill=1)
     oled.display()
     time.sleep(warte)
   
         # Auswertung:
   if P8==1 and P7 == 1 and P6==1 and P5==1 and P4==1 and P3==1 and P2==1 and P1==1:
      draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
      draw.text((5, 5), "BOARD", font=FreeSans30, fill=1)
      draw.text((5, 35), "OK", font=FreeSans30, fill=1)
      oled.display()
      for i in range(15):
         GPIO.output(OK_LED,1)
         time.sleep(0.075)
         GPIO.output(OK_LED,0)
         time.sleep(0.075)
      GPIO.output(OK_LED,1)
   else:
      draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
      draw.text((5, 5), "BOARD", font=FreeSans30, fill=1)
      draw.text((5, 35), "NOK", font=FreeSans30, fill=1)
      oled.display()
      for i in range(15):
         GPIO.output(NOK_LED,1)
         time.sleep(0.075)
         GPIO.output(NOK_LED,0)
         time.sleep(0.075)
      GPIO.output(NOK_LED,1)
              
   x=x+2
   time.sleep(1)
   if x>=1:
       draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
       GPIO.output(NOK_LED,0)
       GPIO.output(OK_LED,0)
       draw.text((10, 2), " Test beendet", font=FreeSans16, fill=1)
       draw.text((10, 25), " Board", font=FreeSans16, fill=1)
       draw.text((10, 45), " entfernen!", font=FreeSans16, fill=1)
       oled.display()
       for i in range(10):
          GPIO.output(OK_LED,0)
          GPIO.output(NOK_LED,1)
          time.sleep(0.075)
          GPIO.output(OK_LED,1)
          GPIO.output(NOK_LED,0)
          time.sleep(0.075)
       time.sleep(2)
       GPIO.output(OK_LED,0)
       teststart()
   else:
      draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
      GPIO.output(NOK_LED,1)
      draw.text((2, 30), "ABBRUCH", font=FreeSans20, fill=1)
      oled.display()
      time.sleep(1)
      pwmLine1.stop(dcCTRLTOP) # AUS
      pwmLine2.stop(dcCTRLTOP) # AUS
      error_error()
      
      #GPIO.Cleanup()
# Hochfahren


draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
draw.text((1, 2), "MD2000-ProWind", font=FreeSans16, fill=1)
oled.display()
draw.text((3, 20), "Platinentester", font=FreeSans20, fill=1)
time.sleep(1)
oled.display()
time.sleep(1)
draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
oled.display()


# Kalibrieren

while k <= 117: #117
    if k==0 or USER_Interrupt ==1:
        USER_interrupt = 0
        draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
        oled.display()
        break  
    proz = str(round((k / 1.17),1)) # proz = String aus gerundeter Zahl mit einer Nachkommastelle.
    draw.text((1, 2), "KALIBRIERPROZESS", font=FreeSans12, fill=1)
    draw.text((2, 50), proz + " %", font=FreeSans12, fill=1)
    draw.text((1, 35), "Nicht berühren!", font=FreeSans12, fill=1)
    k +=1
    draw.line((k, 20, k, 30), fill=1)

    #Frame
    draw.line((1, 18, 121, 18 ), fill=1) #erste Horizontale
    draw.line((1, 32, 121, 32), fill=1) # zweite Horizontale
    draw.line((1, 18, 1, 32), fill=1) # erste vertikale
    draw.line((121, 18, 121, 32), fill=1) # zweite vertikale
    
    oled.display()
    draw.text((2, 50), proz + " %", font=FreeSans12, fill=0)

def Abbruch():
    while (1):
        draw.rectangle((0, 0, 127, oled.height-1), outline=0, fill=0)
        oled.display()
        break  

    

#GPIO.cleanup()  
Tasterabfrage()  


              
# do nothing while waiting for button to be pressed
#while 1:
 #       time.sleep(1)

