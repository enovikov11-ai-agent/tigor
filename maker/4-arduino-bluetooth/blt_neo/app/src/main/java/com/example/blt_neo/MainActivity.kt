package com.example.blt_neo

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import android.bluetooth.BluetoothAdapter
import android.content.Intent
import java.util.UUID


class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        startActivityForResult(Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE), 0);

        Thread(Runnable(){
            run() {
                val bluetooth = BluetoothAdapter.getDefaultAdapter()
                val device = bluetooth.getRemoteDevice("98:D3:32:30:45:A6")
                val socket = device.createRfcommSocketToServiceRecord(UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"))
                socket.connect()
                val stream = socket.outputStream;
                stream.write("hi".toByteArray())
            }
        }).start()

    }
}
