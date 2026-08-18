package com.example.palladium;

import androidx.appcompat.app.AppCompatActivity;

import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.hardware.usb.UsbDevice;
import android.hardware.usb.UsbDeviceConnection;
import android.hardware.usb.UsbManager;
import android.os.Bundle;
import android.util.Log;
import android.webkit.WebView;

import com.felhr.usbserial.UsbSerialDevice;
import com.felhr.usbserial.UsbSerialInterface;

public class USBActivity extends AppCompatActivity {
    private UsbManager usbManager;
    private UsbDevice device;
    private UsbSerialDevice serial;

    private SharedPreferences sharedPreferences;
    private String connectURL;

    private WebView webView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_usb);

        Intent intent = getIntent();
        usbManager = (UsbManager) getSystemService(Context.USB_SERVICE);
        device = (UsbDevice) intent.getParcelableExtra(UsbManager.EXTRA_DEVICE);
        UsbDeviceConnection usbConnection = usbManager.openDevice(device);
        serial = UsbSerialDevice.createUsbSerialDevice(device, usbConnection);

        serial.open();
        serial.setBaudRate(9600);
        serial.setDataBits(UsbSerialInterface.DATA_BITS_8);
        serial.setParity(UsbSerialInterface.PARITY_ODD);
        serial.setFlowControl(UsbSerialInterface.FLOW_CONTROL_OFF);

        sharedPreferences = getSharedPreferences("palladium", MODE_PRIVATE);
        connectURL = sharedPreferences.getString("connectURL", "");

        webView = findViewById(R.id.webView);
        webView.getSettings().setJavaScriptEnabled(true);
        webView.loadUrl(connectURL);
        webView.addJavascriptInterface(new WebAppInterface(serial), "Serial");
    }
}