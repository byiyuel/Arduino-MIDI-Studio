import threading
import time
import mido

class SoloPlayer(threading.Thread):
    def __init__(self, midi_path, buzzer, update_ui_callback, get_settings_callback):
        super().__init__()
        self.midi_path = midi_path
        self.buzzer = buzzer
        self.update_ui = update_ui_callback
        self.get_settings = get_settings_callback # Ayarları okuyan fonksiyon
        self.is_running = True
        self.daemon = True

    def run(self):
        try:
            mid = mido.MidiFile(self.midi_path)
            events = []
            for track in mid.tracks:
                abs_time = 0
                for msg in track:
                    abs_time += msg.time
                    if msg.type in ['note_on', 'note_off', 'set_tempo']:
                        if hasattr(msg, 'channel') and msg.channel == 9: continue
                        events.append({'time': abs_time, 'msg': msg})
            events.sort(key=lambda x: x['time'])

            start_time = time.perf_counter()
            current_tick = 0
            current_tempo = 500000
            active_notes = []

            for event in events:
                if not self.is_running: break
                
                # Ayarları Anlık Olarak Al
                settings = self.get_settings()
                tempo_multiplier = settings['playback_speed']
                transpose = settings['transpose']

                if event['time'] > current_tick:
                    delta = event['time'] - current_tick
                    # Tempo çarpanını bekleme süresine uygula
                    wait = mido.tick2second(delta, mid.ticks_per_beat, current_tempo) / tempo_multiplier
                    target = start_time + wait
                    
                    while time.perf_counter() < target and self.is_running:
                        # Beklerken notayı çal (Transpoze eklenmiş haliyle)
                        if active_notes:
                            self.play_note(active_notes[-1], transpose)
                        else:
                            self.play_note(0, 0)
                        time.sleep(0.01)
                    
                    start_time = target
                    current_tick = event['time']

                msg = event['msg']
                if msg.type == 'set_tempo':
                    current_tempo = msg.tempo
                else:
                    note = msg.note
                    vel = msg.velocity if msg.type == 'note_on' else 0
                    if msg.type == 'note_on' and vel > 0:
                        if note in active_notes: active_notes.remove(note)
                        active_notes.append(note)
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and vel == 0):
                        if note in active_notes: active_notes.remove(note)

            self.buzzer.send_freq(0)
            self.update_ui("BİTTİ", False)

        except Exception as e:
            self.update_ui(f"Hata: {e}", False)

    def play_note(self, note, transpose):
        if note > 0:
            final_note = note + transpose
            # Nota 0-127 arasında kalmalı
            if final_note < 0: final_note = 0
            if final_note > 127: final_note = 127
            
            freq = self.buzzer.midi_to_freq(final_note)
            self.buzzer.send_freq(freq)
            name = self.buzzer.get_note_name(final_note)
            self.update_ui(f"{name} | {freq} Hz", True)
        else:
            self.buzzer.send_freq(0)
            self.update_ui("...", False)

    def stop(self):
        self.is_running = False
