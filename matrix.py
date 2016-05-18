""" Matrix Screen Effect
"""
from itertools import chain
from itertools import product
from math import sqrt
from os.path import join
from random import random, randrange, choice

import pygame

# Configuration
charset = """abcdefghijklmnopqrstuvwxzy0123456789$+-*/=%"'#&_(),.;:?!\|{}<>[]^~"""
font_name = join('resources', 'matrix code nfi.otf')
font_size = 32
screen_size = 640, 480
glyph_width = 14
glyph_height = 16
grid_spacing_x = 2
grid_spacing_y = 2
streamers = 0
logo = None
computed_values = list()


class Glyph(pygame.sprite.Sprite):
    value = 0
    pos = 0, 0
    image = None
    char = None
    ttl = 0
    char_index = 0


class XYGroup(object):
    def __init__(self):
        self.layout = list()
        self.sprites = list()

    @property
    def active_sprites(self):
        return (i for i in self.sprites if i.value)

    def draw(self, surface):
        for sprite in self.active_sprites:
            surface.blit(sprite.image, sprite.pos)


def main():
    # singletons, kinda
    global screen_size
    max_streamers = 30
    grid = XYGroup()
    cache = list()
    frame_number = 0
    save_to_disk = 0

    def get_glyph_image(glyph):
        return cache[glyph.index][glyph.ttl]

    def calc_color(value):
        value *= 255.
        if value > 190:
            value = int(round(value))
            value2 = int((value * 255) / 300)
            return value2, value, value2
        else:
            value2 = int((value * 255) / 800)
            value = int((value * 255.) / 300.)
            return value2, value, value2

    def new_glyph(font):
        glyph = Glyph()
        glyph.value = choice(computed_values)
        glyph.index = randrange(len(charset))
        glyph.image = get_glyph_image(glyph)
        return glyph

    def burn_glyph(glyph):
        glyph.ttl = 0
        glyph.value = 1
        x = glyph.pos[0] // (glyph_width + grid_spacing_x)
        y = glyph.pos[1] // (glyph_height + grid_spacing_y)
        burn_set.add((x, y, glyph))

    def update_grid():
        for glyph in grid.active_sprites:
            if random() > .9:
                glyph.index = randrange(len(charset))
            glyph.ttl += 1
            glyph.value = computed_values[glyph.ttl]
            glyph.image = get_glyph_image(glyph)

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

        while not (streamers > max_streamers or random() > .5):
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

        grid.sprites = [i for i in chain.from_iterable(data)]
        grid.layout = data

    pygame.init()
    pygame.font.init()

    scanline = pygame.Surface((glyph_width, glyph_height), pygame.SRCALPHA)
    for y in range(0, glyph_height, 2):
        pygame.draw.line(scanline, (0, 0, 0, 128), (0, y), (glyph_width, y))

    time = 0.
    duration = 5000.
    while 1:
        a = 1
        b = 0
        prog = min(1., time / duration)
        p = prog - 1.0
        t = sqrt(1.0 - p * p)
        value = (a * (1. - t)) + (b * t)
        computed_values.append(value)
        time += 16
        if prog >= 1:
            break

    screen = init_screen(*screen_size)
    font = pygame.font.Font(font_name, font_size)
    for index, char in enumerate(charset):
        chars = list()
        cache.append(chars)
        for value in computed_values:
            color = calc_color(value)
            image = font.render(char, 1, color)
            image = pygame.transform.smoothscale(image, (glyph_width, glyph_height))
            image.blit(scanline, (0, 0))
            back = pygame.Surface(image.get_size())
            back.blit(image, (0, 0))
            chars.append(back)

    burn_set = set()
    init_group(*screen_size)
    clock = pygame.time.Clock()

    running = True
    while running:
        clock.tick()

        for event in pygame.event.get():
            if event.type == pygame.VIDEORESIZE:
                if not screen_size == (event.w, event.h):
                    screen_size = event.w, event.h
                screen = init_screen(*screen_size)
                init_group(*screen_size)

            elif event.type == pygame.QUIT:
                running = False

        update_grid()
        grid.draw(screen)
        screen.blit(logo, (0, 0), None, pygame.BLEND_RGBA_MULT)

        if save_to_disk:
            filename = "snapshot%05d.tga" % frame_number
            frame_number += 1
            pygame.image.save(screen, filename)

        pygame.display.flip()


if __name__ == "__main__":
    main()
