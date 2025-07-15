import pygame as pg
from engine_antiantilopa import *
from fast_gameobject_creator import *
from synth import *
import os


Synths.seconds_per_note = 0.4

width = 20

e = Engine((1000, 800))

scene = create_game_object(tags="scene", at=Position.CENTER, size=(1000, 2200))

music_sec = create_game_object(scene, "music_sec", InGrid((width, 1), (1, 0), (width-1, 1)), color=ColorComponent.WHITE, shape=Shape.RECT)

note_sec = create_game_object(scene, "note_sec", InGrid((width, 1), (0, 0), (1, 1)), color=ColorComponent.BLUE, shape=Shape.RECT)

scroll = 0
#          sin tri sqr nos

playing: pg.mixer.Channel = None

tones_list: list[list[int]] = [[], [], [], []]

for m in range(4):
    if os.path.exists(f"raw{m}"):
        notes = Note.load_notes_new(f"raw{m}")
        for note in notes:
            if note.pause:
                tones_list[m].append(int(89 - 1 + Note.minimal_tone))
            else:
                tones_list[m].append(note.tone)
            for _ in range(int(note.duration) - 1):
                tones_list[m].append(None)

mode = 0

colors = ((0, 255, 0), (255, 0, 0), (255, 128, 0), (0, 0, 255), (128, 255, 128), (255, 128, 128), (255, 255, 128), (128, 128, 255))

for i in range(89):
    if i == 89 - 1:
        note_obj = create_game_object(note_sec, ["note", -1], InGrid((1, 89), (0, 89-1), (1, 1)), color=ColorComponent.PURPLE, shape=Shape.RECT, margin=Vector2d(1, 1))
        create_label(note_obj, "note_label", "stop", at = Position.LEFT, color=ColorComponent.RED)
    else:
        note = Note(0, i + Note.minimal_tone)
        note_obj = create_game_object(note_sec, ["note", i], InGrid((1, 89), (0, i), (1, 1)), color=[note.get_color() * 200] * 3, shape=Shape.RECT, margin=Vector2d(1, 1))
        note_obj.add_component(OnClickComponent([1, 0, 0], 0, 1, lambda g, k, p, n: Synths.play_arr(Synths.get_sin_arr(n.freq, 0.5), 0), note))

        create_label(note_obj, "note_label", str(i + Note.minimal_tone), at = Position.LEFT, color=ColorComponent.RED)

def click(g_obj: GameObject, keys: tuple[bool, bool, bool], pos: Vector2d):
    global scroll, tones_list, mode, cells

    if g_obj.get_component(PosComponent).pos.inty() != 89 - 1: 
        Synths.play_arr(Synths.get_tri_arr(Note(1, g_obj.get_component(PosComponent).pos.inty() + Note.minimal_tone).freq, 0.1), 0)

    if keys[0]:
        if g_obj.get_component(ColorComponent).color == colors[mode]:
            return
        if len(tones_list[mode]) <= scroll + g_obj.get_component(PosComponent).pos.x:
            for _ in range(scroll + g_obj.get_component(PosComponent).pos.intx() - len(tones_list[mode]) + 1):
                tones_list[mode].append(None)
        tones_list[mode][scroll + g_obj.get_component(PosComponent).pos.intx()] = g_obj.get_component(PosComponent).pos.inty() + Note.minimal_tone
    if keys[2]:
        if g_obj.get_component(ColorComponent).color == ColorComponent.BLACK:
            return
        if scroll + g_obj.get_component(PosComponent).pos.intx() == len(tones_list[mode]) - 1:
            tones_list[mode].pop(-1)
        else:
            tones_list[mode][scroll + g_obj.get_component(PosComponent).pos.intx()] = None
    update_cells_color()


def update_cells_color():
    global scroll, cells, tones_list
    for pos in VectorRange(Vector2d(0, 0), Vector2d(width, 89)):
        cells[pos.inty()][pos.intx()].get_component(ColorComponent).color = ColorComponent.BLACK
        cells[pos.inty()][pos.intx()].need_draw = True
        cells[pos.inty()][pos.intx()].need_blit_set_true()
    
    last_ys = [-1] * 4
    for m in range(4):
        for i in range(min(len(tones_list[m]) - scroll, width)):
            if tones_list[m][i + scroll] is None:
                j = 1
                while last_ys[m] == -1:
                    if i + scroll - j >= len(tones_list[m]) or i + scroll - j < 0:
                        last_ys[m] = -2
                    elif tones_list[m][i + scroll - j] is not None:
                        last_ys[m] = tones_list[m][i + scroll - j] - Note.minimal_tone
                    j += 1
                if last_ys[m] == -2:
                    continue
                cells[last_ys[m]][i].get_component(ColorComponent).color = colors[m + 4]
            else:
                cells[tones_list[m][i + scroll] - Note.minimal_tone][i].get_component(ColorComponent).color = colors[m]
                last_ys[m] = tones_list[m][i + scroll] - Note.minimal_tone
            
def do_scroll(g_obj: GameObject, keys: list[int]):
    global scroll
    if pg.K_RIGHT in keys:
        scroll += 1
        update_cells_color()
    elif pg.K_LEFT in keys:
        if scroll == 0:
            return
        scroll -= 1
        update_cells_color()
    elif pg.K_l in keys:
        scroll = 0
        update_cells_color()
    elif pg.K_r in keys:
        scroll = max([len(tones) for tones in tones_list]) - width
        update_cells_color()
    if pg.K_UP in keys:
        scene.get_component(Transform).move(Vector2d(0, +30))
    elif pg.K_DOWN in keys:
        scene.get_component(Transform).move(Vector2d(0, -30))

music_sec.add_component(KeyBindComponent([pg.K_RIGHT, pg.K_LEFT, pg.K_UP, pg.K_DOWN, pg.K_l, pg.K_r], 1, 1, do_scroll))

def change_mod(g_obj: GameObject, keys: list[int]):
    global mode
    if pg.K_1 in keys:
        mode = 0
    if pg.K_2 in keys:
        mode = 1
    if pg.K_3 in keys:
        mode = 2
    if pg.K_4 in keys:
        mode = 3

music_sec.add_component(KeyBindComponent([pg.K_1, pg.K_2, pg.K_3, pg.K_4], 0, 1, change_mod))

def save(g_obj: GameObject, keys: list[int]):
    global tones_list

    notes = [[], [], [], []]

    for m in range(4):
        if len(tones_list[m]) == 0:
            continue
        t = tones_list[m][0]
        d = 1
        for tone in tones_list[m][1:]:
            if tone is None:
                d += 1
            else:
                if t is not None:
                    if t == 89 + Note.minimal_tone - 1:
                        notes[m].append(Note(d, 0, 1))
                    else:
                        notes[m].append(Note(d, t))
                else:
                    notes[m].append(Note(d, 0, 1))
                t = tone
                d = 1
        if t == 89 + Note.minimal_tone - 1:
            notes[m].append(Note(d, 0, 1))
        else:
            notes[m].append(Note(d, t))

        Note.save_notes(notes[m], f"melody_part_{m + 1}")
        Note.save_notes_new(notes[m], f"raw{m}")

music_sec.add_component(KeyBindComponent([pg.K_q], 0, 1, save))

def play(g_obj: GameObject, keys: list[int]):
    global tones_list, playing

    if playing is not None:
        playing.stop()

    notes = [[], [], [], []]

    for m in range(4):
        if len(tones_list[m]) == 0:
            continue
        t = tones_list[m][0]
        d = 1
        for tone in tones_list[m][1:]:
            if tone is None:
                d += 1
            else:
                if t is not None:
                    if t == 89 + Note.minimal_tone - 1:
                        notes[m].append(Note(d, 0, 1))
                    else:
                        notes[m].append(Note(d, t))
                else:
                    notes[m].append(Note(d, 0, 1))
                t = tone
                d = 1
        if t == 89 + Note.minimal_tone - 1:
            notes[m].append(Note(d, 0, 1))
        else:
            notes[m].append(Note(d, t))
    
    party1 = Synths.get_tri_party(notes[0])
    party2 = Synths.get_tri_party(notes[1])
    party3 = Synths.get_sqr_party(notes[2])

    music = Synths.merge_parties(party1, party2, party3)

    playing = Synths.play_arr(music, delay=0, loops=-1)

music_sec.add_component(KeyBindComponent([pg.K_p], 0, 1, play))

cells: list[list[GameObject]] = [[None for i in range(width)] for j in range(89)]

class PosComponent(Component):
    pos:Vector2d
    def __init__(self, pos: Vector2d):
        super().__init__()
        self.pos = pos

for pos in VectorRange(Vector2d(0, 0), Vector2d(width, 89)):
    cell = create_game_object(music_sec, "cell", at=InGrid((width, 89), (pos.x, pos.y), (1, 1)), margin=Vector2d(3, 3), color=ColorComponent.BLACK, shape=Shape.RECT)
    cell.add_component(OnClickComponent([1, 0, 1], 1, 0, click))
    cell.add_component(PosComponent(pos))
    cells[pos.inty()][pos.intx()] = cell

# bind_keys_for_camera_movement(speed=30)

update_cells_color()

e.run()