# 🎵 Arduino MIDI Studio

Arduino'ya bağlı pasif bir buzzer üzerinden `.mid` dosyalarını gerçek zamanlı çalan, Python tabanlı masaüstü MIDI oynatıcısı. Modern karanlık temalı arayüzü, canlı Arduino telemetrisi ve iki farklı oynatma modu ile tam bir MIDI stüdyosu deneyimi sunar.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Arduino](https://img.shields.io/badge/Arduino-Uno%2FNano-teal?logo=arduino)
![License](https://img.shields.io/badge/License-MIT-green)
![Version](https://img.shields.io/badge/Version-4.5-orange)

---

## ✨ Özellikler

- 🎹 **MIDI Oynatma** — Standart `.mid` dosyalarını okur ve MIDI zamanlamasına sadık kalarak çalar
- 🎛️ **İki Oynatma Modu:**
  - **Solo Modu** — Aktif notalar arasından en son basılı olanı çalar, tek sesli melodi için idealdir
  - **Chiptune (Arpej) Modu** — Aynı anda basılı birden fazla notayı hızla arpejileyerek retro 8-bit efekti yaratır
- 🎚️ **Gerçek Zamanlı Ayarlar** — Oynatma sırasında hız, transpoz ve arpej hızını anında değiştirebilirsiniz
- 📡 **Arduino Telemetrisi** — Chip sıcaklığı, boş RAM ve çalışma süresi bilgilerini canlı izler
- 🖥️ **Modern Arayüz** — Tkinter ile yapılmış karanlık tema, LCD ekran simülasyonu ve hover efektli butonlar
- 🔌 **Kolay Bağlantı** — Seri port listesini otomatik tarar, tek tıkla bağlanır

---

## 🔧 Donanım Gereksinimleri

| Bileşen | Açıklama |
|---|---|
| Arduino Uno / Nano | ATmega328P tabanlı herhangi bir model |
| Pasif Buzzer | **Aktif buzzer değil!** Pasif buzzer frekans kontrolüne izin verir |
| Jumper Kablo | 2 adet |

### Devre Şeması

```
Arduino Pin 8  ──────────  Buzzer (+)
Arduino GND    ──────────  Buzzer (-)
```

> ⚠️ **Not:** Farklı bir pin kullanmak isterseniz `arduino_buzzer_player.ino` dosyasındaki `BUZZER_PIN` değerini değiştirin.

---

## 💻 Kurulum

### 1. Depoyu Klonlayın

```bash
git clone https://github.com/kullanici-adi/arduino-midi-studio.git
cd arduino-midi-studio
```

### 2. Python Bağımlılıklarını Kurun

```bash
pip install mido pyserial
```

### 3. Arduino Kodunu Yükleyin

1. `arduino_buzzer_player.ino` dosyasını Arduino IDE'de açın
2. Arduino'nuzu bilgisayara bağlayın
3. Doğru kartı ve portu seçin
4. **Yükle** butonuna tıklayın

### 4. Uygulamayı Başlatın

```bash
python main.py
```

---

## 🚀 Kullanım

1. **Port Seç** — Açılır menüden Arduino'nun bağlı olduğu seri portu seçin ve **Bağlan**'a tıklayın
2. **MIDI Dosyası Seç** — "Dosya Seç" butonu ile bir `.mid` dosyası yükleyin
3. **Mod Seç** — Solo veya Chiptune modunu seçin
4. **Ayarları Yapın** — Hız, transpoz ve arpej hızı sliderlarını istediğiniz gibi ayarlayın
5. **▶ OYNAT** — Başlatın ve ekranda o an çalınan notayı izleyin

### Oynatma Modları Karşılaştırması

| Özellik | Solo Modu | Chiptune Modu |
|---|---|---|
| Aynı anda çalınan ses | Tek | Tek (ama arpejli) |
| Çoklu nota desteği | Son basılan nota | Notalar sırayla döner |
| Kullanım amacı | Melodi çalma | Retro / 8-bit efekti |
| Ek ayar | — | Arpej Hızı (ms) |

---

## ⚙️ Ayarlar

| Ayar | Aralık | Açıklama |
|---|---|---|
| Oynatma Hızı | 0.5× – 3.0× | MIDI temposunu hızlandırır / yavaşlatır |
| Transpoz | -24 – +24 | Tüm notaları yarım ton olarak kaydırır |
| Arpej Hızı | 20 – 500 ms | Chiptune modunda notalar arası geçiş süresi |

---

## 📄 Lisans

Bu proje MIT Lisansı ile lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.