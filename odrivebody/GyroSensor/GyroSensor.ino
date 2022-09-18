#include <MPU6050_tockn.h>
#include <Wire.h>

// MPU6050 Library: https://github.com/tockn/MPU6050_tockn

MPU6050 mpu6050(Wire);

unsigned long lastSerial = millis();
int sendInterval = 10; // ms

void setup() {
  Serial.begin(115200);
  
  mpu6050.begin();
  // See Readme for gyro calibration
  // mpu6050.calcGyroOffsets(true);
  mpu6050.setGyroOffsets(-1.70, -0.12, 0.04); // change these values
}

void loop() {
    mpu6050.update();

    // showDebug();
    if(millis() - lastSerial > sendInterval) {
      sendYAngleToSerial();
      lastSerial = millis();
    }
}

void sendYAngleToSerial() {
    float yAngleChange = mpu6050.getGyroY();
    float yAngle = mpu6050.getAccAngleY();
    
    Serial.print(yAngle);
    Serial.print(" ");
    Serial.println(yAngleChange);
}

void showDebug() {
    Serial.println("=======================================================");
    Serial.print("temp : ");Serial.println(mpu6050.getTemp());
    Serial.print("accX : ");Serial.print(mpu6050.getAccX());
    Serial.print("\taccY : ");Serial.print(mpu6050.getAccY());
    Serial.print("\taccZ : ");Serial.println(mpu6050.getAccZ());
  
    Serial.print("gyroX : ");Serial.print(mpu6050.getGyroX());
    Serial.print("\tgyroY : ");Serial.print(mpu6050.getGyroY());
    Serial.print("\tgyroZ : ");Serial.println(mpu6050.getGyroZ());
  
    Serial.print("accAngleX : ");Serial.print(mpu6050.getAccAngleX());
    Serial.print("\taccAngleY : ");Serial.println(mpu6050.getAccAngleY());
  
    Serial.print("gyroAngleX : ");Serial.print(mpu6050.getGyroAngleX());
    Serial.print("\tgyroAngleY : ");Serial.print(mpu6050.getGyroAngleY());
    Serial.print("\tgyroAngleZ : ");Serial.println(mpu6050.getGyroAngleZ());
    
    Serial.print("angleX : ");Serial.print(mpu6050.getAngleX());
    Serial.print("\tangleY : ");Serial.print(mpu6050.getAngleY());
    Serial.print("\tangleZ : ");Serial.println(mpu6050.getAngleZ());
    Serial.println("=======================================================\n");
}
