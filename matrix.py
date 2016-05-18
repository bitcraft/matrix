""" Matrix Screen Effect
"""
from itertools import chain
from itertools import product
from os.path import join
from random import randint, choice

import pygame

from animation import Animation

# Configuration
charset = """abcdefghijklmnopqrstuvwxzy0123456789$+-*/=%"'#&_(),.;:?!\|{}<>[]^~"""
font_name = join('resources', 'matrix code nfi.otf')
font_size = 32
screen_size = 640, 480
glyph_width = 14
glyph_height = 16
grid_spacing_x = 2
grid_spacing_y = 2


class Glyph(pygame.sprite.Sprite):
    value = 0
    pos = 0, 0
    image = None
    char = None
    index = 0


class XYGroup(object):
    def __init__(self):
        self.layout = list()
        self.q = None

    def __iter__(self):
        for y, row in enumerate(self.layout):
            for x, sprite in enumerate(row):
                if sprite.value:
                    yield x, y, sprite

    def sprites(self):
        return [i for i in chain.from_iterable(self.layout) if i.value]

    def draw(self, surface):
        for sprite in self.sprites():
            surface.blit(sprite.image, sprite.pos)


streamers = 0
logo = None
computed_values = list()


def main():
    # singletons, kinda
    global screen_size
    max_streamers = 30
    grid = XYGroup()
    cache = dict()
    frame_number = 0
    save_to_disk = 0

    def render_glyph(font, glyph):
        color = calc_color(glyph.value)
        char = glyph.char
        try:
            return cache[(char, color)]

        except KeyError:
            image = font.render(char, 1, color)
            image = pygame.transform.smoothscale(image, (glyph_width, glyph_height))
            image.blit(scanline, (0, 0))
            back = pygame.Surface(image.get_size())
            back.blit(image, (0, 0))
            cache[(char, color)] = back
            return back

    def calc_color(value):
        value = int(round(value * 255., 0))
        if value > 190:
            value2 = int((value * 255) / 300)
            return value2, value, value2
        else:
            value2 = int((value * 255) / 800)
            value = int((value * 255.) / 300.)
            return value2, value, value2

    def new_glyph(font):
        glyph = Glyph()
        glyph.value = choice(computed_values)
        glyph.char = choice(charset)
        glyph.image = render_glyph(font, glyph)
        return glyph

    def burn_glyph(glyph):
        glyph.index = 0
        glyph.value = 1
        x = glyph.pos[0] // (glyph_width + grid_spacing_x)
        y = glyph.pos[1] // (glyph_height + grid_spacing_y)
        burn_set.add((x, y, glyph))

    def update_grid():
        for glyph in grid.sprites():
            if not randint(0, 80):
                glyph.char = choice(charset)
            glyph.index += 1
            glyph.value = computed_values[glyph.index]
            glyph.image = render_glyph(font, glyph)

        global streamers
        old_set = burn_set.copy()
        to_remove = set()
        for token in old_set:
            x, y, glyph = token
            if glyph.value < .85:
                to_remove.add(token)
                try:
                    new = grid.layout[y + 1][x]
                    burn_glyph(new)
                except IndexError:
                    streamers -= 1

        burn_set.difference_update(to_remove)

        while not (streamers > max_streamers or randint(0, 2)):
            glyph = choice(grid.layout[0])
            burn_glyph(glyph)
            streamers += 1

    def init_screen(width, height):
        return pygame.display.set_mode((width, height), pygame.RESIZABLE)

    def init_group(width, height):
        global logo

        cell_x = glyph_width + grid_spacing_x
        cell_y = glyph_height + grid_spacing_y
        cell_width = int(width // cell_x)
        cell_height = int(height // cell_y)

        logo = pygame.image.load(join('resources', 'python.png')).convert_alpha()
        logo = pygame.transform.smoothscale(logo, (width, height))

        data = [[None] * cell_width for i in range(cell_height)]
        for y, x in product(range(cell_height), range(cell_width)):
            glyph = new_glyph(font)
            glyph.pos = x * cell_x, y * cell_y
            data[y][x] = glyph
            if glyph.value > .95:
                burn_glyph(glyph)
        grid.layout = data

    pygame.init()
    pygame.font.init()

    scanline = pygame.Surface((glyph_width, glyph_height), pygame.SRCALPHA)
    for y in range(0, glyph_height, 2):
        pygame.draw.line(scanline, (0, 0, 0, 128), (0, y), (glyph_width, y))

    dummy = Glyph()
    ani = Animation(dummy, value=0, initial=1, duration=5000, transition='out_circ')
    group = pygame.sprite.Group()
    group.add(ani)
    while len(group):
        ani.update(16)
        computed_values.append(dummy.value)

    burn_set = set()
    screen = init_screen(*screen_size)
    font = pygame.font.Font(font_name, font_size)
    init_group(*screen_size)
    clock = pygame.time.Clock()

    running = True
    while running:
        clock.tick()
        print(clock.get_fps())

        # trials:
        # 1: 40 fps
        # 2: 50 fps
        # 3: 80 fps
        # 4: 90 fps

        for event in pygame.event.get():
            if event.type == pygame.VIDEORESIZE:
                if not screen_size == (event.w, event.h):
                    screen_size = event.w, event.h
                screen = init_screen(*screen_size)
                init_group(*screen_size)

            elif event.type == pygame.QUIT:
                running = False

        update_grid()
        screen.fill((0, 0, 0))
        grid.draw(screen)
        screen.blit(logo, (0, 0), None, pygame.BLEND_RGBA_MULT)

        if save_to_disk:
            filename = "snapshot%05d.tga" % frame_number
            frame_number += 1
            pygame.image.save(screen, filename)

        pygame.display.flip()


if __name__ == "__main__":
    main()
