import pygame
import numpy as np
import time
import wave

pygame.init()
pygame.mixer.init(channels=2)

class Note:
    duration: float
    tone: int
    pause: bool

    half_tone = np.pow(2, 1/12)
    minimal_tone = -48
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    colors = (1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1)
    def __init__(self, duration: float, tone: int, pause: bool = False):
        self.duration = duration
        self.tone = tone
        self.pause = pause
        self.freq = 440 * (Note.half_tone ** tone)
    
    def __repr__(self):
        return f"{Note.names[(self.tone + 9) % 12]}\t{4 + (self.tone + 9) // 12}\t{self.duration}"

    def get_color(self):
        return Note.colors[(self.tone + 9) % 12]
    
    @staticmethod
    def save_notes(notes: list["Note"], name: str):
        with open(f"{name}.txt", "w") as f:
            for note in notes:
                f.write(f"{note.duration}/{note.tone}/{int(note.pause)}\n")
    
    @staticmethod
    def load_notes(name: str):
        notes = []
        with open(f"{name}.txt", "r") as f:
            for string in f.read().split("\n")[:-1]:
                dur = float(string.split("/")[0])
                tone = int(string.split("/")[1])
                pause = int(string.split("/")[2])
                notes.append(Note(dur, tone, pause))
        return notes
    
    def save_notes_new(notes: list["Note"], name: str):
        with open(f"{name}", "wb") as f:
            for note in notes:
                if note.pause == 1:
                    write = 255
                else:
                    write = note.tone - Note.minimal_tone
                f.write(bytes((int(note.duration), write)))
    
    @staticmethod
    def load_notes_new(name: str) -> list["Note"]:
        notes = []
        with open(f"{name}", "rb") as f:
            raw = f.read()
            assert len(raw) % 2 == 0
            for i in range(len(raw) // 2):
                dur = int(raw[2 * i])
                tone = int(raw[2 * i + 1] + Note.minimal_tone)
                pause = (raw[2 * i + 1] == 255)
                notes.append(Note(dur, tone, pause))
        return notes


class Synths:
    rate: int = 44100
    seconds_per_note: float = 0.4
    cache = {}

    def __init__(self, rate: int = 44100):
        Synths.rate = rate
    
    @staticmethod
    def get_control_arr(duration = 1.5):
        if ("get_control_arr", duration) in Synths.cache:
            return Synths.cache[("get_control_arr", duration)]
        rate = Synths.rate
        up = np.linspace(0, 1, round(0.01 * rate))
        straight = np.full(round((duration * rate) - 2 * round(0.01 * rate)), 1)
        down = np.linspace(1, 0, round((0.01) * rate))
        Synths.cache[("get_control_arr", duration)] = np.append(np.append(up, straight), down)
        return Synths.cache[("get_control_arr", duration)]

    @staticmethod
    def get_attack_arr(duration = 1.5):
        if ("get_attack_arr", duration) in Synths.cache:
            return Synths.cache[("get_attack_arr", duration)]
        rate = Synths.rate
        up = np.linspace(0, 1, round(0.01 * rate))
        down = np.linspace(1, 0, round((duration * rate) - round(0.01 * rate)))
        Synths.cache[("get_attack_arr", duration)] = np.append(up, down)
        return Synths.cache[("get_attack_arr", duration)]
    
    @staticmethod
    def get_hit_attack_arr(duration = 1.5):
        if ("get_hit_attack_arr", duration) in Synths.cache:
            return Synths.cache[("get_hit_attack_arr", duration)]
        rate = Synths.rate
        up = np.linspace(0, 1, round(0.01 * rate))
        down = np.linspace(1, 0.2, round(0.01 * rate))
        steep_down = np.linspace(0.2, 0, round((duration * rate) - round(0.01 * rate) - round(0.01 * rate)))
        Synths.cache[("get_hit_attack_arr", duration)] = np.append(np.append(up, down), steep_down)
        return Synths.cache[("get_hit_attack_arr", duration)]

    @staticmethod
    def get_sin_arr(freq, duration = 1.5):
        if ("get_sin_arr", freq, duration) in Synths.cache:
            return Synths.cache[("get_sin_arr", freq, duration)]
        rate = Synths.rate
        t = np.linspace(0, duration, round(rate * duration), endpoint=False)
        arr = np.sin(2 * np.pi * freq * t)
        arr *= Synths.get_control_arr(duration)
        Synths.cache[("get_sin_arr", freq, duration)] = arr
        return arr

    @staticmethod
    def get_pin_arr(freq, duration = 1.5):
        if ("get_pin_arr", freq, duration) in Synths.cache:
            return Synths.cache[("get_pin_arr", freq, duration)]
        rate = Synths.rate
        t = np.linspace(0, duration, round(rate * duration), endpoint=False)
        arr = np.sin(2 * np.pi * freq * t) / 2
        for i in range(2, 10):
            arr += np.sin(2 * np.pi * freq * t * 2 ** i) / (2 ** i)
        arr *= Synths.get_control_arr(duration)
        Synths.cache[("get_pin_arr", freq, duration)] = arr
        return arr
    
    @staticmethod
    def get_pqr_arr(freq, duration = 1.5):
        if ("get_pqr_arr", freq, duration) in Synths.cache:
            return Synths.cache[("get_pqr_arr", freq, duration)]
        rate = Synths.rate
        t = np.linspace(0, duration, round(rate * duration), endpoint=False)
        arr = np.fmod(np.floor(t * freq), 2) / 2
        for i in range(2, 4):
            arr += np.fmod(np.floor(t * freq * 2 ** i), 2) / (2 ** i)
        arr *= Synths.get_control_arr(duration)
        Synths.cache[("get_pqr_arr", freq, duration)] = arr
        return arr

    @staticmethod
    def get_tri_arr(freq, duration = 1.5):
        if ("get_tri_arr", freq, duration) in Synths.cache:
            return Synths.cache[("get_tri_arr", freq, duration)]
        rate = Synths.rate
        t = np.linspace(0, duration, round(rate * duration), endpoint=False)
        arr = np.fmod(t * freq / 2, 1)
        arr *= Synths.get_control_arr(duration)
        # arr /= 3
        Synths.cache[("get_tri_arr", freq, duration)] = arr
        return arr
    
    @staticmethod
    def get_sqr_arr(freq, duration = 1.5):
        if ("get_sqr_arr", freq, duration) in Synths.cache:
            return Synths.cache[("get_sqr_arr", freq, duration)]
        rate = Synths.rate
        t = np.linspace(0, duration, round(rate * duration), endpoint=False)
        arr = np.fmod(np.floor(t * freq), 2)
        arr *= Synths.get_control_arr(duration)
        # arr /= 3
        Synths.cache[("get_sqr_arr", freq, duration)] = arr
        return arr

    @staticmethod
    def get_nos_arr(duration = 1.5):
        if ("get_nos_arr", duration) in Synths.cache:
            return Synths.cache[("get_nos_arr", duration)]
        rate = Synths.rate
        arr = np.random.rand(round(rate * duration))
        arr *= Synths.get_control_arr(duration)
        Synths.cache[("get_nos_arr", duration)] = arr
        return arr
    
    @staticmethod
    def get_hit_arr(duration = 1.5):
        if ("get_hit_arr", duration) in Synths.cache:
            return Synths.cache[("get_hit_arr", duration)]
        rate = Synths.rate
        arr = np.random.rand(round(rate * duration))
        arr *= Synths.get_hit_attack_arr(duration)
        Synths.cache[("get_hit_arr", duration)] = arr
        return arr

    @staticmethod
    def get_non_arr(duration = 1.5):
        rate = Synths.rate
        arr = np.zeros(round(duration * rate))
        return arr

    @staticmethod
    def play_arr(arr, delay: bool = True, loops = 0) -> pygame.mixer.Channel:
        sound = np.asarray([32767 * arr, 32767 * arr]).T.astype(np.int16)
        sound = pygame.sndarray.make_sound(sound.copy())
        sound_channel = sound.play(loops=loops)
        if delay:
            pygame.time.delay(len(arr) * 1000 // Synths.rate)
        return sound_channel
    
    @staticmethod
    def save_to_wav(arr, output_filename = "output_sound.wav"):
        sound = np.asarray([32767 * arr, 32767 * arr]).T.astype(np.int16)
        sound = pygame.sndarray.make_sound(sound.copy())
        
        with wave.open(output_filename, 'wb') as wf:
            # Set WAV file parameters
            wf.setnchannels(2)  # Number of channels (e.g., 1 for mono, 2 for stereo)
            wf.setsampwidth(2)  # Sample width in bytes (e.g., 2 for 16-bit)
            wf.setframerate(Synths.rate)  # Frame rate (frequency)

            # Write the raw audio data
            wf.writeframes(sound.get_raw())

    @staticmethod
    def get_sin_party(notes: list[Note]):
        res = np.empty(sum([round(Synths.rate * note.duration * Synths.seconds_per_note) for note in notes]))
        i = 0
        for note in notes:
            if note.pause:
                arr = Synths.get_non_arr(note.duration * Synths.seconds_per_note)
            else:
                arr = Synths.get_sin_arr(note.freq, note.duration * Synths.seconds_per_note)
            res[i : i + round(Synths.rate * note.duration * Synths.seconds_per_note)] = arr
            i += round(Synths.rate * note.duration * Synths.seconds_per_note)
        return res

    @staticmethod
    def get_pin_party(notes: list[Note]):
        res = np.empty(sum([round(Synths.rate * note.duration * Synths.seconds_per_note) for note in notes]))
        i = 0
        for note in notes:
            if note.pause:
                arr = Synths.get_non_arr(note.duration * Synths.seconds_per_note)
            else:
                arr = Synths.get_pin_arr(note.freq, note.duration * Synths.seconds_per_note)
            res[i : i + round(Synths.rate * note.duration * Synths.seconds_per_note)] = arr
            i += round(Synths.rate * note.duration * Synths.seconds_per_note)
        return res

    @staticmethod
    def get_pqr_party(notes: list[Note]):
        res = np.empty(sum([round(Synths.rate * note.duration * Synths.seconds_per_note) for note in notes]))
        i = 0
        for note in notes:
            if note.pause:
                arr = Synths.get_non_arr(note.duration * Synths.seconds_per_note)
            else:
                arr = Synths.get_pqr_arr(note.freq, note.duration * Synths.seconds_per_note)
            res[i : i + round(Synths.rate * note.duration * Synths.seconds_per_note)] = arr
            i += round(Synths.rate * note.duration * Synths.seconds_per_note)
        return res

    @staticmethod
    def get_tri_party(notes: list[Note]):
        res = np.empty(sum([round(Synths.rate * note.duration * Synths.seconds_per_note) for note in notes]))
        i = 0
        for note in notes:
            if note.pause:
                arr = Synths.get_non_arr(note.duration * Synths.seconds_per_note)
            else:
                arr = Synths.get_tri_arr(note.freq, note.duration * Synths.seconds_per_note)
            res[i : i + round(Synths.rate * note.duration * Synths.seconds_per_note)] = arr
            i += round(Synths.rate * note.duration * Synths.seconds_per_note)
        return res
    
    @staticmethod
    def get_sqr_party(notes: list[Note]):
        res = np.empty(sum([round(Synths.rate * note.duration * Synths.seconds_per_note) for note in notes]))
        i = 0
        for note in notes:
            if note.pause:
                arr = Synths.get_non_arr(note.duration * Synths.seconds_per_note)
            else:
                arr = Synths.get_sqr_arr(note.freq, note.duration * Synths.seconds_per_note)
            res[i : i + round(Synths.rate * note.duration * Synths.seconds_per_note)] = arr
            i += round(Synths.rate * note.duration * Synths.seconds_per_note)
        return res
    
    @staticmethod
    def get_nos_party(notes: list[Note]):
        res = np.empty(sum([round(Synths.rate * note.duration * Synths.seconds_per_note) for note in notes]))
        i = 0
        for note in notes:
            if note.pause:
                arr = Synths.get_non_arr(note.duration * Synths.seconds_per_note)
            else:
                arr = Synths.get_nos_arr(note.duration * Synths.seconds_per_note)
            res[i : i + round(Synths.rate * note.duration * Synths.seconds_per_note)] = arr
            i += round(Synths.rate * note.duration * Synths.seconds_per_note)
        return res
    
    @staticmethod
    def get_hit_party(notes: list[Note]):
        res = np.empty(sum([round(Synths.rate * note.duration * Synths.seconds_per_note) for note in notes]))
        i = 0
        for note in notes:
            if note.pause:
                arr = Synths.get_non_arr(note.duration * Synths.seconds_per_note)
            else:
                arr = Synths.get_hit_arr(note.duration * Synths.seconds_per_note)
            res[i : i + round(Synths.rate * note.duration * Synths.seconds_per_note)] = arr
            i += round(Synths.rate * note.duration * Synths.seconds_per_note)
        return res

    @staticmethod
    def merge_parties(*parties: list):
        max_len = 0
        for party in parties:
            if len(party) > max_len:
                max_len = len(party)
        
        res = np.zeros(max_len)
        for party in parties:
            res += np.append(party, np.zeros(max_len - len(party)))
        
        res /= len(parties)

        return res

if __name__ == "__main__":

    Synths.seconds_per_note = 0.4

    start = time.time()
    print(f"start: {start}")

    # tones1 = []
    # with open("moonlight_sonata.txt", "r") as f:
    #     for t in f.read().split("\n"):
    #         tones1.append(int(t))

    # notes1 = [Note(1, t) for t in tones1]

    # Note.save_notes(notes1, "moonlight_melody")

    # tones2 = [(-8, 4), (-10, 4), (-12, 2), (-15, 2), (-13, 2), (-13, 2), (-8, 4), (-9, 4), (-8, 2), (-3, 2), (-10, 2), (-10, 1), (-10, 1), (-5, 4), (-5, 4), (-7, 4), (-9, 1), (-10, 1), (-11, 1), (-10, 1), (-10, 2), (-17, 1), (-14, 1), (-15, 2), (-15, 2), (-10, 5), (-5, 1), (-2, 1), (-5, 1), (-10, 5), (-5, 1), (-2, 1), (-5, 1), (-10, 2), (-13, 2), (-16, 2), (-15, 2), (-10, 2), (-9, 2), (-20, 2), (-20, 1), (-20, 1), (-15, 4), (-4, 4), (-3, 2), (-6, 1), (-8, 1), (-9, 3) ,(-9, 1), (-8, 2), (-15, 1), (-14, 1), (-13, 4), (-13, 4), (-13, 4), (-13, 4), (-13, 4), (-13, 4), (-13, 4), (-13, 12), (-13, 4), (-13, 4), (-13, 2), (-12, 2), (-15, 2), (-13, 2), (-8, 4), (-9, 4), (-8, 2), (-15, 2), (-10, 2), (-10, 1), (-10, 1), (-5, 4)]
    # notes2 = [Note(1 * tone[1] * 3, tone[0]) for tone in tones2]

    # Note.save_notes(notes2, "moonlight_accompany")


    notes1 = Note.load_notes_new("1")
    notes2 = Note.load_notes_new("2")

    beats = [(0.5, 0.1), (0, 0.9)] * (len(notes1) // 3)
    notes3 = []

    # notes1.reverse()
    # notes2.reverse()
    # notes3.reverse()

    sin_part = Synths.get_pin_party(notes2)
    tri_part = Synths.get_pin_party(notes1)
    # sqr_part = Synths.get_tri_party(notes2)
    # dun_part = Synths.get_sqr_party(notes1)
    # nos_part = Synths.get_nos_party(notes3)

    party = Synths.merge_parties(sin_part, tri_part)

    # party /= 10

    end = time.time()
    print(f"diff: {end - start}")
    print(f"end: {end}")

    Synths.play_arr(party, 0, -1)
    # Synths.save_to_wav(party, "moonlight_saw.wav")
    while True:pass

