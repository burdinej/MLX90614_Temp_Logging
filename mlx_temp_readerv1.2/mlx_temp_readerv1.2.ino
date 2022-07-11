/*!
   @file        mlx_temp_reader.ino
   @brief       fill this in
   @license     The MIT License (MIT)
   @author      Joshua Burdine for LANL nEDM
   @version     V1.2
   @date        06/09/2022
   @url         fill this in
*/
#include <DFRobot_MLX90614.h>

const byte MLX90614_IIC_ADDR = 0x5A; // mlx96014 default IIC communication address
// Custom i2c follower addresses
const byte MLX1_I2C_ADDR = 0x0A;
const byte MLX2_I2C_ADDR = 0x0B;

// Serial commands
const char ack = 'H';
const char dataCMD = 'B';
const char stopCMD = 'E';
const char setEmisCMD = 'S';
const char getEmisCMD = 'G';
const char endLine = '\n';

// Flags
bool firstDataReq = false;
bool hsFlag = false;

// instantiate objects to drive sensors
DFRobot_MLX90614_IIC sensor1(MLX1_I2C_ADDR, &Wire);
DFRobot_MLX90614_IIC sensor2(MLX2_I2C_ADDR, &Wire);

// Clears the read buffer. If user writes to arduino while clearing buffer, this will
// eventually timeout and cause hard fault or stop.
void serial_clear()
{
  int i = 0;
  while (Serial.available() > 0)
  {
    char del = Serial.read();
    i++;
    if (i > 100) {
      break;  // consider this a timeout condition incase user keeps spamming shit, probably stop cmd then
    }
  }
  return;
}

// Initialize desired sensors
void initialize_sensor(int dev)
{
  switch (dev) {
    case 1:
      if (NO_ERR != sensor1.begin()) {
        Serial.print("Initialization error: can't connect to device. Sensor 1");
        Serial.print(endLine);
        hsFlag = false;
        
      }
      break;
    case 2:
      if (NO_ERR != sensor2.begin()) {
        Serial.print("Initialization error: can't connect to device. Sensor 2");
        Serial.print(endLine);
        hsFlag = false;
      }
      break;
  }
  return;
}

// Closes sensor serial comms
void stop_data ()
{
  hsFlag = false;
  sleepSensor1();
  sleepSensor2();
  Serial.print("Serial to sensors closed !...");
  Serial.print(endLine);
  Serial.flush();
  return ;
}

// Returns an ambient and distant object temp measurement from each sensor
void get_data()
{
  // Data sent as amb1,obj1,amb2,obj2\n
  Serial.print(sensor1.getAmbientTempCelsius());
  Serial.print(','); // delimeter
  Serial.print(sensor1.getObjectTempCelsius());
  Serial.print(',');
  Serial.print(sensor2.getAmbientTempCelsius());
  Serial.print(',');
  Serial.print(sensor2.getObjectTempCelsius());
  Serial.print(endLine);
  Serial.flush();
  return;
}

// Next two functions cycle desired sensor between sleep and then back awake
// If sensor already asleep, this will just wake up
void resetSensor1()
{
  sensor1.enterSleepMode();
  delay(200);
  sensor1.enterSleepMode(false);
  delay(600);
  return;
}

void resetSensor2()
{
  sensor2.enterSleepMode();
  delay(200);
  sensor2.enterSleepMode(false);
  delay(600);
  return;
}

void sleepSensor1() 
{
  sensor1.enterSleepMode();
  delay(100);
  return;
}

void sleepSensor2()
{
  sensor2.enterSleepMode();
  delay(100);
  return;
}


// Sets desired Emissivity to desired device
void set_emissivity(int dev, float emis)
{
  switch (dev) {
    case 1:
      sensor1.setEmissivityCorrectionCoefficient(emis);
      resetSensor1();
      Serial.print("Emissivity on sensor 1 set to ");
      Serial.print(emis);
      Serial.print(" !");
      Serial.print(endLine);
      Serial.flush();
      break;
    case 2:
      sensor2.setEmissivityCorrectionCoefficient(emis);
      resetSensor2();
      Serial.print("Emissivity on sensor 2 set to ");
      Serial.print(emis);
      Serial.print(" !");
      Serial.print(endLine);
      Serial.flush();
      break;
    default:
      Serial.print("Error: invalid input (dev, emis): ");
      Serial.print(dev);
      Serial.print(", ");
      Serial.print(emis);
      Serial.print(endLine);
      Serial.flush();
  }
  return;
}

// Reads value at sensor emissivity register address, formats and returns float from 0.1 to 1.0 to user
void get_emissivity(int dev)
{
  float emis = -1;
  switch (dev) {
    case 1:
      emis = sensor1.getEmissivityCorrectionCoefficient();
      break;
    case 2:
      emis = sensor2.getEmissivityCorrectionCoefficient();
      break;
  }
  Serial.print("Current emissivity on sensor ");
  Serial.print(dev);
  Serial.print(" is: ");
  Serial.print(emis);
  Serial.print(endLine);
  Serial.flush();
  return;
}

// Parses comms for command and executes accordingly
void executeCMD() {
  char cmd = Serial.read();
  
  if (cmd == dataCMD) {               // Starts data logging
    if (firstDataReq == false) {
      Serial.print("Arduino received request to log! Starting data collection...");
      Serial.print(endLine);
      Serial.flush();
      serial_clear();
      firstDataReq = true;
    }
    get_data();
  }
  else if (cmd == stopCMD) {          // Stops data collection and closes sensor connection
    Serial.print("Arduino received stop command! Stopping data logging and closing sensor comms...");
    Serial.print(endLine);
    Serial.flush();
    stop_data();
  }
  else if (cmd == setEmisCMD) {       // Parses out desired device and emissivity, configures sensor accordingly
    delay(1000);
    float emis = Serial.parseFloat();
    int dev = Serial.parseInt();
    Serial.print("Arduino received request to set emissivity on sensor ");
    Serial.print(dev);
    Serial.print(" to ");
    Serial.print(emis);
    Serial.print(" ! Setting emissivity...");
    Serial.print(endLine);
    Serial.flush();
    serial_clear();
    set_emissivity(dev, emis);
  }
  else if (cmd == getEmisCMD) {       // Returns the device's current emissivity setting to the user
    int dev = Serial.parseInt();
    Serial.print("Arduino received request to get current emissivity of sensor ");
    Serial.print(dev);
    Serial.print(" ! Getting emissivity...");
    Serial.print(endLine);
    Serial.flush();
    serial_clear();
    get_emissivity(dev);
  }
  return;
}

// Establishes communication w/ user program and initializes sensors
void startHandshake() {
  initialize_sensor(1);
  initialize_sensor(2);
  resetSensor1();
  resetSensor2();
  Serial.print("Sensors initalized! Ready!");
  Serial.print(endLine);
  Serial.flush();

  return;
}

// Start Serial port at 115200 Baud rate
void setup()
{
  Serial.begin(115200);
}

// Wait for communication from user program. Establish handshake to initialize, if done, then execute cmd
void loop()
{
  if (Serial.available()) {                      // Wait till there is some comm
    if (hsFlag == false) {                       // Check to see if handshake established
      if (Serial.peek() == ack) {                // check to see if handshake is requested
        serial_clear();
        hsFlag = true;
        startHandshake();
      }
      else {                                    // Need to handshake, throw error
        Serial.read();
        Serial.print("You need to initialize sensors first! Restart!");
        Serial.print(endLine);
        Serial.flush();
        serial_clear();
      }
    }
    else {                                      // We have handshake, so this is a cmd
      executeCMD();
      hsFlag = true;
    }
  }
}
