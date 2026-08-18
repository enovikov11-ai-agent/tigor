package com.example.palladium;

import android.webkit.JavascriptInterface;

import com.felhr.usbserial.UsbSerialDevice;

public class WebAppInterface {
    private UsbSerialDevice mSerial;

    WebAppInterface(UsbSerialDevice serial) {
        mSerial = serial;
    }

    @JavascriptInterface
    public void write(String data) {
        mSerial.write(data.getBytes());
    }
}