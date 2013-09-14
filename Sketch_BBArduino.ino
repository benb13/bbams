/*
 Code:           Sketch_BBArduino
 Version:        13.07.02
 Author:         Benjamin Bordonaro
 Library Credits:
 Library originally added 18 Apr 2008 by David A. Mellis
 Library modified 5 Jul 2009 by Limor Fried (http://www.ladyada.net)
 Based on example added 9 Jul 2009 by Tom Igoe
 Modified 22 Nov 2010 by Tom Igoe
 Circuit Layout:
 * DS18B20 (temperature) data to digital pin 6
 * --- LCD PINS ---
 * Set LCD Pins (RS, EN, D4, D5, D6, D7) 
 * LiquidCrystal lcd(7, 8, 2, 3, 4, 9);
 * X10 Pins - For future use
 * zcPin 11
 * dataPin 10
 */
 
#include <LiquidCrystal.h> 
#include <OneWire.h>
#include <DallasTemperature.h>
 
// Data wire is plugged into pin 6 on the Arduino
#define ONE_WIRE_BUS 6
 
// Define X10 Pins - For later use
#define zcPin 11
#define dataPin 10
 
// Global Variables to turn on and off hardware control
#define LCD_ENABLE 1    // LCD
#define LED_ENABLE 0    // LED
#define EML_ENABLE 1    // Email Checking and Display
#define TMP_ENABLE 1    // Temperature Sensor Display
 
// Setup a oneWire instance to communicate with any OneWire devices (not just Maxim/Dallas temperature ICs)
OneWire oneWire(ONE_WIRE_BUS);
 
// Pass our oneWire reference to Dallas Temperature. 
DallasTemperature sensors(&oneWire);
 
// Set LCD Pins (RS, EN, D4, D5, D6, D7) 
LiquidCrystal lcd(7, 8, 2, 3, 4, 9);
 
DeviceAddress ts1, ts2, ts3, ts4;
// function to print a device address
void printAddress(DeviceAddress deviceAddress)
{
  for (uint8_t i = 0; i < 8; i++)
  {
    // zero pad the address if necessary
    if (deviceAddress[i] < 8) lcd.print("0");
    lcd.print(deviceAddress[i]);
  }
}
 
void serialReader(){
  int makeSerialStringPosition;
  int inByte;
  String serialReadString;
  String stringOne;
  const int terminatingChar = 13; //Terminate lines with CR
 
  inByte = Serial.read();
  makeSerialStringPosition=0;
 
  if (inByte > 0 && inByte != terminatingChar) { //If we see data (inByte > 0) and that data isn't a carriage return
    delay(100); //Allow serial data time to collect (I think. All I know is it doesn't work without this.)
 
    while (inByte != terminatingChar && Serial.available() > 0){ // As long as EOL not found and there's more to read, keep reading
      serialReadString[makeSerialStringPosition] = inByte; // Save the data in a character array
 
      makeSerialStringPosition++; //Increment position in array
      //if (inByte > 0) Serial.println(inByte); // Debug line that prints the charcodes one per line for everything recieved over serial
      inByte = Serial.read(); // Read next byte
    }
 
    if (inByte == terminatingChar) //If we terminated properly
    {
      serialReadString[makeSerialStringPosition] = 0; //Null terminate the serialReadString (Overwrites last position char (terminating char) with 0
        if (makeSerialStringPosition > 1) {
          stringOne = serialReadString;
          int firstListItem = stringOne.indexOf("|");
          int secondListItem = stringOne.indexOf("|", firstListItem + 1 );
          String Line1 = "";
          String Line2 = "";
          String Line3 = "";
          for (int strPos = 0; strPos < firstListItem; strPos++) { 
            Line1 = Line1 + stringOne.charAt(strPos);
          }
          //Serial.println(Line1);
          lcd.setCursor(0, 0);
          lcd.print(Line1);
          for (int strPos = firstListItem +1 ; strPos < secondListItem; strPos++) { 
            Line2 = Line2 + stringOne.charAt(strPos);
          }
          //Serial.println(Line2);
          lcd.setCursor(0, 1);
          lcd.print(Line2);
              for (int strPos = secondListItem +1 ; strPos < stringOne.length(); strPos++) { 
            Line3 = Line3 + stringOne.charAt(strPos);
          }
          //Serial.println(Line3);
          lcd.setCursor(0, 2);
          lcd.print(Line3);
        }
    }
  } 
}
 
 
void setup()
{
  Serial.begin(9600);  
  // IC Default 9 bit. If you have troubles consider upping it 12. 
  // Up the delay giving the IC more time to process the temperature measurement
  if (TMP_ENABLE)
  {  
    sensors.begin();
    int sensorCnt = sensors.getDeviceCount();
    sensors.getAddress(ts1, 0);
  }
  if (LCD_ENABLE)
  {
    // Setup the LCD
    //lcd.begin(16, 2); 
    lcd.begin(20, 4); 
    lcd.setCursor(0, 3);
    lcd.print("Temp (F)");
  }
}
 
void loop()
{
  if (TMP_ENABLE)
  {  
    delay(1000);          //waiting 1 second
    // request to all devices on the bus
    sensors.requestTemperatures(); // Send the command to get temperatures
    float temperature1 = (((sensors.getTempCByIndex(0)) * 1.8 ) + 32);
    int tempSensorValue = int(temperature1);
    if (temperature1 > 0)
    {
      Serial.println(temperature1); 
      if (LCD_ENABLE)
      { 
        lcd.setCursor(0, 3);
        lcd.print("Temp (F)");
        lcd.setCursor(15, 3);
        lcd.print(temperature1);
      }
    }
    else
    {
      Serial.println(temperature1);
    }
    delay(5000);  //waiting 5 seconds
  }
  // See if any data is on the serial port
  lcd.setCursor(0, 1);
  serialReader();
}
