#include <ESP8266WiFi.h>
#include "sha256.c"
#include <stdio.h>

int bits_count_8[256], bits_count_4[256];

void init_calc()
{
  for (int i = 0; i < 256; i++)
  {
    bits_count_8[i] = 0;
    for (int j = 0; j < 8; j++)
    {
      if ((1 << j) & i)
      {
        bits_count_8[i]++;
      }
    }

    bits_count_4[i] = 0;
    for (int j = 4; j < 8; j++)
    {
      if ((1 << j) & i)
      {
        bits_count_4[i]++;
      }
    }
  }
}

int calc_exponent(String seed)
{
  SHA256_CTX ctx;
  BYTE hash[32];

  sha256_init(&ctx);
  sha256_update(&ctx, (const BYTE *)seed.c_str(), seed.length());
  sha256_final(&ctx, hash);

  // 100 = 12 * 8 + 4
  int ones = bits_count_8[hash[0]] + bits_count_8[hash[1]] + bits_count_8[hash[2]] + bits_count_8[hash[3]] +
             bits_count_8[hash[4]] + bits_count_8[hash[5]] + bits_count_8[hash[6]] + bits_count_8[hash[7]] +
             bits_count_8[hash[8]] + bits_count_8[hash[9]] + bits_count_8[hash[10]] + bits_count_8[hash[11]] +
             bits_count_4[hash[12]];

  return ones - 2 * (100 - ones);
}

void setup()
{
  init_calc();

  WiFi.mode(WIFI_AP_STA);
  WiFi.disconnect();
  delay(100);
}

void loop()
{
  int n = WiFi.scanNetworks();
  for (int i = 0; i < n; ++i)
  {
    String ssid = WiFi.SSID(i);

    if (ssid.substring(0, 7) == "vas100 ")
    {
      String seed = ssid.substring(7);
      int exp = calc_exponent(seed);
      char result[256];

      snprintf(result, 256, "🎲(%s) = 2 ** %d", seed.c_str(), exp);
      WiFi.softAP(result);
        }
  }
}
