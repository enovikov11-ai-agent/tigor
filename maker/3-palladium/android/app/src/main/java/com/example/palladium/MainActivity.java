package com.example.palladium;

import androidx.appcompat.app.AppCompatActivity;

import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.View;
import android.widget.EditText;
import android.widget.Toast;

public class MainActivity extends AppCompatActivity {
    private SharedPreferences sharedPreferences;
    private SharedPreferences.Editor editor;
    private EditText serverURLEdit;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        sharedPreferences = getSharedPreferences("palladium", MODE_PRIVATE);
        editor = sharedPreferences.edit();

        serverURLEdit = findViewById(R.id.serverURL);
        String connectURL = sharedPreferences.getString("connectURL", "");
        serverURLEdit.setText(connectURL);
    }

    public void onSetURLClick(View view) {
        editor.putString("connectURL", serverURLEdit.getText().toString());
        editor.commit();
        Toast.makeText(getApplicationContext(), "Server URL set ok", Toast.LENGTH_SHORT).show();
    }
}