/*
 * MIDI to Arduino Buzzer Player
 * 
 * Bu Arduino kodu Python scriptinden gelen notaları buzzer ile çalar.
 * 
 * Bağlantı:
 * - Buzzer (+) pini -> Arduino Pin 8
 * - Buzzer (-) pini -> Arduino GND
 * 
 * Seri Port Formatı: "FREQUENCY,DURATION\n"
 * Örnek: "440,200\n" -> 440 Hz frekansı 200 ms boyunca çal
 *        "0,0\n" -> Sesi durdur
 */

#define BUZZER_PIN 8  // Buzzer'ın bağlı olduğu pin

void setup() {
  // Seri portu başlat
  Serial.begin(9600);
  
  // Buzzer pinini çıkış olarak ayarla
  pinMode(BUZZER_PIN, OUTPUT);
  
  // Başlangıç sinyali
  Serial.println("Arduino Buzzer Player hazir!");
  
  // Başlangıç melodisi (opsiyonel)
  tone(BUZZER_PIN, 1000, 100);
  delay(150);
  tone(BUZZER_PIN, 1500, 100);
  delay(150);
  noTone(BUZZER_PIN);
}

void loop() {
  // Seri porttan veri gelip gelmediğini kontrol et
  if (Serial.available() > 0) {
    // Satır sonuna kadar oku
    String data = Serial.readStringUntil('\n');
    data.trim();  // Boşlukları temizle
    
    // Virgül ile ayır
    int commaIndex = data.indexOf(',');
    if (commaIndex > 0) {
      // Frekans ve süre değerlerini al
      String freqStr = data.substring(0, commaIndex);
      String durStr = data.substring(commaIndex + 1);
      
      int frequency = freqStr.toInt();
      int duration = durStr.toInt();
      
      // Debug için seri porta yazdır
      Serial.print("Freq: ");
      Serial.print(frequency);
      Serial.print(" Hz, Dur: ");
      Serial.print(duration);
      Serial.println(" ms");
      
      // Frekans 0 ise sesi durdur
      if (frequency == 0) {
        noTone(BUZZER_PIN);
      } 
      // Aksi halde notayı çal
      else {
        // Duration 0 ise sürekli çal
        if (duration == 0) {
          tone(BUZZER_PIN, frequency);
        } 
        // Duration verilmişse belirtilen süre boyunca çal
        else {
          tone(BUZZER_PIN, frequency, duration);
        }
      }
    }
  }
}

/*
 * NOTLAR:
 * 
 * 1. tone() fonksiyonu:
 *    - tone(pin, frequency) -> Sürekli çalar
 *    - tone(pin, frequency, duration) -> Belirtilen süre boyunca çalar
 * 
 * 2. noTone() fonksiyonu:
 *    - noTone(pin) -> Sesi durdurur
 * 
 * 3. Frekans Aralığı:
 *    - Arduino tone() fonksiyonu 31 Hz - 65535 Hz arası çalışır
 *    - İnsan kulağı yaklaşık 20 Hz - 20000 Hz arası duyar
 *    - Piyano notaları: 27.5 Hz (A0) - 4186 Hz (C8)
 * 
 * 4. Buzzer Seçimi:
 *    - Pasif buzzer kullanılmalıdır (aktif buzzer tek frekans çalar)
 *    - Pasif buzzer frekans kontrolü sağlar
 * 
 * 5. Alternatif Pin:
 *    - Buzzer'ı farklı bir pine bağlarsanız BUZZER_PIN değerini değiştirin
 *    - PWM destekli pinler: 3, 5, 6, 9, 10, 11 (Uno için)
 */
