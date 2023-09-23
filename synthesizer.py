import pygame
import sys
import numpy as np
import scipy.signal

# Pygame initialisieren
pygame.init()

# Audio-Setup
sample_rate = 44100  # Samples pro Sekunde
pygame.mixer.pre_init(sample_rate, -16, 1, 512)
pygame.mixer.init()

# Frequenzen für jede Note
frequencies = {
    'C': 261.63,
    'C#': 277.18,
    'D': 293.66,
    'D#': 311.13,
    'E': 329.63,
    'F': 349.23,
    'F#': 369.99,
    'G': 392.00,
    'G#': 415.30,
    'A': 440.00,
    'A#': 466.16,
    'B': 493.88,
}

# Wellenformen
waveforms = ['sine', 'square', 'sawtooth', 'triangle']
current_waveform = 'sine'

# Initialisiere ADSR-Parameter
adsr_params = {
    'attack': 0.1,
    'decay': 0.1,
    'sustain': 0.5,
    'release': 0.1,
}

# Filterparameter initialisieren
filter_type = 'LPF'  # Mögliche Werte: 'HPF', 'BPF', 'LPF'
frequency = 1000  # Hz
min_frequency = 100  # Minimaler Wert der Frequenz, den der Drehregler annehmen kann
max_frequency = 20000  # Maximaler Wert der Frequenz, den der Drehregler annehmen kann
resonance = 0.5  # Wert zwischen 0 und 1

def apply_filter(tone, filter_type, frequency, resonance, sample_rate):
    # Berechne den Q-Faktor aus der Resonanz
    q_factor = 1 / resonance
    
    # Erstelle das Hauptfilter
    b, a = None, None
    if filter_type == 'LPF':
        b, a = scipy.signal.iirfilter(2, frequency / (sample_rate / 2), btype='lowpass', ftype='butter')
    elif filter_type == 'HPF':
        b, a = scipy.signal.iirfilter(2, frequency / (sample_rate / 2), btype='highpass', ftype='butter')
    elif filter_type == 'BPF':
        b, a = scipy.signal.iirfilter(2, [frequency / (sample_rate / 2), frequency / (sample_rate / 2)], btype='bandpass', ftype='butter')
    
    # Wende das Hauptfilter auf den Ton an
    filtered_tone = scipy.signal.lfilter(b, a, tone)

    # Erstelle und wende das Resonanzfilter an
    b_res, a_res = scipy.signal.iirpeak(frequency / (sample_rate / 2), 1/q_factor)
    resonant_tone = scipy.signal.lfilter(b_res, a_res, filtered_tone)
    
    return np.int16(resonant_tone * 32767)

# Funktion zum Erzeugen von Tönen
def generate_tone(frequency):
    t = np.linspace(0, 1, sample_rate, False)
    
    # Wähle die Wellenform basierend auf current_waveform
    if current_waveform == 'sine':
        tone = 0.5 * np.sin(2 * np.pi * frequency * t)
    elif current_waveform == 'square':
        tone = 0.5 * np.sign(np.sin(2 * np.pi * frequency * t))
    elif current_waveform == 'sawtooth':
        tone = 0.5 * scipy.signal.sawtooth(2 * np.pi * frequency * t)
    elif current_waveform == 'triangle':
        tone = 0.5 * scipy.signal.sawtooth(2 * np.pi * frequency * t, width=0.5)
    
    stereo_tone = np.vstack((tone, tone)).T
    c_contiguous_tone = np.ascontiguousarray(stereo_tone)
    return np.int16(c_contiguous_tone * 32767)

def apply_envelope(tone, adsr_params, sample_rate):
    total_samples = len(tone)
    attack_samples = int(adsr_params['attack'] * sample_rate)
    decay_samples = int(adsr_params['decay'] * sample_rate)
    release_samples = int(adsr_params['release'] * sample_rate)
    sustain_samples = total_samples - attack_samples - decay_samples - release_samples
    
    if sustain_samples < 0:
        attack_samples = max(0, attack_samples + sustain_samples // 3)
        decay_samples = max(0, decay_samples + sustain_samples // 3)
        sustain_samples = max(0, sustain_samples)
        release_samples = max(0, total_samples - attack_samples - decay_samples - sustain_samples)
    
    envelope = np.ones(total_samples)
    envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
    envelope[attack_samples:attack_samples+decay_samples] = np.linspace(1, adsr_params['sustain'], decay_samples)
    envelope[attack_samples+decay_samples:attack_samples+decay_samples+sustain_samples] = adsr_params['sustain']
    envelope[attack_samples+decay_samples+sustain_samples:] = np.linspace(adsr_params['sustain'], 0, release_samples)
    
    # Erweitere das envelope-Array auf die gleiche Form wie tone
    envelope = np.vstack((envelope, envelope)).T

    return np.int16(tone * envelope)

# Fenstergröße festlegen
width = 350
height = 400

# Fenster erstellen
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Digitaler Synthesizer')

# Farben definieren
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Klaviatur erstellen
#weiße Tasten
keys = [
    {'rect': pygame.Rect(0, 0, 50, 200), 'color': WHITE, 'note': 'C'},
    {'rect': pygame.Rect(50, 0, 50, 200), 'color': WHITE, 'note': 'D'},
    {'rect': pygame.Rect(100, 0, 50, 200), 'color': WHITE, 'note': 'E'},
    {'rect': pygame.Rect(150, 0, 50, 200), 'color': WHITE, 'note': 'F'},
    {'rect': pygame.Rect(200, 0, 50, 200), 'color': WHITE, 'note': 'G'},
    {'rect': pygame.Rect(250, 0, 50, 200), 'color': WHITE, 'note': 'A'},
    {'rect': pygame.Rect(300, 0, 50, 200), 'color': WHITE, 'note': 'B'},
]
#schwarze Tasten
keys.extend([
    {'rect': pygame.Rect(35, 0, 30, 120), 'color': BLACK, 'note': 'C#'},
    {'rect': pygame.Rect(85, 0, 30, 120), 'color': BLACK, 'note': 'D#'},
    {'rect': pygame.Rect(185, 0, 30, 120), 'color': BLACK, 'note': 'F#'},
    {'rect': pygame.Rect(235, 0, 30, 120), 'color': BLACK, 'note': 'G#'},
    {'rect': pygame.Rect(285, 0, 30, 120), 'color': BLACK, 'note': 'A#'},
])

# Haupt-Schleife
running = True
dragging = None  # speichert, welcher Schieberegler gerade bewegt wird
dragging_knob = None  # speichert, welcher Drehregler gerade bewegt wird
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for key in keys:
                if key['rect'].collidepoint(event.pos):
                    tone = generate_tone(frequencies[key['note']])
                    tone = apply_envelope(tone, adsr_params, sample_rate)
                    tone = apply_filter(tone, filter_type, frequency, resonance, sample_rate)
                    sound = pygame.sndarray.make_sound(tone)
                    sound.play()

            # Überprüfe, ob eines der Wellenform-Buttons geklickt wurde
            mouse_x, mouse_y = pygame.mouse.get_pos()
            for i, waveform in enumerate(waveforms):
                if pygame.Rect(10, 210 + i*30, 100, 25).collidepoint(mouse_x, mouse_y):
                    current_waveform = waveform

            # Überprüfe, ob eines der ADSR-Schieberegler geklickt wurde
            for i, param in enumerate(adsr_params):
                thumb_rect = pygame.Rect(130, 210 + i * 30, 10, 25)
                if thumb_rect.collidepoint(mouse_x, mouse_y):
                    dragging = param

            # Überprüfe, ob eines der Filter-Auswahlfelder geklickt wurde
            for filter_option in ['HPF', 'BPF', 'LPF']:
                option_rect = pygame.Rect(260, 210 + ['HPF', 'BPF', 'LPF'].index(filter_option) * 30, 60, 25)
                if option_rect.collidepoint(event.pos):
                    filter_type = filter_option

            # Überprüfe, ob einer der Drehregler geklickt wurde
            if pygame.Rect(250, 300, 40, 40).collidepoint(event.pos):  # Großer Drehregler
                dragging_knob = 'frequency'
            elif pygame.Rect(300, 300, 20, 20).collidepoint(event.pos):  # Kleiner Drehregler
                dragging_knob = 'resonance'

        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = None
            dragging_knob = None
        elif event.type == pygame.MOUSEMOTION and dragging is not None:
            # Bewege den Thumb des Schiebereglers und aktualisiere den ADSR-Wert
            _, mouse_y = pygame.mouse.get_pos()
            adsr_params[dragging] = max(0, min(1, (mouse_y - (210 + list(adsr_params).index(dragging) * 30)) / 25))

        elif event.type == pygame.MOUSEMOTION and dragging_knob is not None:
            # Bewege den Drehregler und aktualisiere den Filterwert
            _, mouse_y = pygame.mouse.get_pos()
            if dragging_knob == 'frequency':
                frequency = max(100, min(20000, frequency + (mouse_y - 300) * 10))  # Begrenze den Frequenzbereich
            elif dragging_knob == 'resonance':
                resonance = max(0, min(1, resonance + (mouse_y - 300) * 0.01))  # Begrenze den Resonanzbereich

    # Bildschirm aktualisieren
    screen.fill(BLACK)
    for key in keys:
        pygame.draw.rect(screen, key['color'], key['rect'])
        pygame.draw.line(screen, BLACK, key['rect'].topright, key['rect'].bottomright, 3)
    

    # Zeichne Wellenform-Buttons
    for i, waveform in enumerate(waveforms):
        pygame.draw.rect(screen, WHITE if waveform == current_waveform else BLACK, (10, 210 + i*30, 100, 25))
        font = pygame.font.Font(None, 36)
        text = font.render(waveform, True, BLACK if waveform == current_waveform else WHITE)
        screen.blit(text, (15, 210 + i*30))

    # Zeichne ADSR-Schieberegler
    for i, param in enumerate(adsr_params):
        pygame.draw.rect(screen, WHITE, (120, 210 + i * 30, 30, 25))  # Hintergrund
        thumb_y = 210 + i * 30 + adsr_params[param] * 25
        pygame.draw.rect(screen, BLACK, (130, thumb_y, 10, 25))  # Thumb
        font = pygame.font.Font(None, 36)
        text = font.render(param, True, WHITE)
        screen.blit(text, (160, 210 + i * 30))

    # Zeichne Filter-Auswahlfelder und Drehregler
    for filter_option in ['HPF', 'BPF', 'LPF']:
        option_rect = pygame.Rect(260, 210 + ['HPF', 'BPF', 'LPF'].index(filter_option) * 30, 60, 25)
        pygame.draw.rect(screen, WHITE if filter_option == filter_type else BLACK, option_rect)
        font = pygame.font.Font(None, 36)
        text = font.render(filter_option, True, BLACK if filter_option == filter_type else WHITE)
        screen.blit(text, (265, 210 + ['HPF', 'BPF', 'LPF'].index(filter_option) * 30))

    # Großer Drehregler für die Frequenz
    pygame.draw.circle(screen, WHITE, (270, 320), 20)
    angle = 2 * np.pi * (frequency - min_frequency) / (max_frequency - min_frequency) - np.pi / 2
    x = 270 + int(15 * np.cos(angle))
    y = 320 + int(15 * np.sin(angle))
    pygame.draw.line(screen, BLACK, (270, 320), (x, y), 2)

    # Kleiner Drehregler für die Resonanz
    pygame.draw.circle(screen, WHITE, (310, 320), 10)
    angle = 2 * np.pi * resonance - np.pi / 2
    x = 310 + int(7 * np.cos(angle))
    y = 320 + int(7 * np.sin(angle))
    pygame.draw.line(screen, BLACK, (310, 320), (x, y), 2)

    pygame.display.flip()

# Pygame beenden
pygame.quit()
sys.exit()
