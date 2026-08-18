// ESP32 Dev Module

#include "driver/gpio.h"
#include "soc/gpio_struct.h"
#include "soc/io_mux_reg.h"
#include "soc/gpio_reg.h"
#include "esp_rom_sys.h"
#include "esp_system.h"

int delay_us = 2000;
int pins[] = {5, 18, 19, 21};
const int pinCount = sizeof(pins) / sizeof(pins[0]);

int pinActive = 0;
int task = 0;

void updateState() {
    for (int i = 0; i < pinCount; i++) {
        if (i == pinActive) {
            REG_WRITE(GPIO_OUT_W1TS_REG, (1 << pins[i]));
        } else {
            REG_WRITE(GPIO_OUT_W1TC_REG, (1 << pins[i]));
        }
    }
}

void setup() {
  Serial.begin(9600);

  for (int i = 0; i < pinCount; i++) {
    gpio_reset_pin((gpio_num_t)pins[i]);
    gpio_set_direction((gpio_num_t)pins[i], GPIO_MODE_OUTPUT);
  }

  updateState();
}

void loop() { 
    if (Serial.available()) {
        task = Serial.parseInt();
    }

    while (task != 0) {
        if (task > 0) {
            task--;
            pinActive = (pinActive + 3) % 4;
        } else if (task < 0) {
            task++;
            pinActive = (pinActive + 1) % 4;
        }

        updateState();

        esp_rom_delay_us(delay_us);
    }    
}
