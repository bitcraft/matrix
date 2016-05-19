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
logo = None
computed_values = list()
max_streamers = 0


class Glyph(pygame.sprite.Sprite):
    value = 0
    pos = 0, 0
    image = None
    char = None
    ttl = 0
    index = 0


class XYGroup(object):
    def __init__(self):
        self.layout = list()
        self.sprites = list()

    @property
    def active_sprites(self):
        return (i for i in self.sprites if i.ttl < len(computed_values))

    def draw(self, surface):
        for sprite in self.active_sprites:
            surface.blit(sprite.image, sprite.pos)


def main():
    # singletons, kinda
    global screen_size
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
        glyph.ttl = randrange(len(computed_values))
        glyph.index = randrange(len(charset))
        glyph.image = get_glyph_image(glyph)
        return glyph

    def burn_glyph(glyph):
        glyph.ttl = 0
        glyph.image = get_glyph_image(glyph)
        burn_set.add(glyph)

    def update_grid():
        for glyph in grid.active_sprites:
            if random() > .9:
                glyph.index = randrange(len(charset))
            glyph.ttl += 1
            if glyph.ttl == len(computed_values):
                glyph.image = None
            else:
                glyph.image = get_glyph_image(glyph)

        old_set = burn_set.copy()
        to_remove = set()
        for glyph in old_set:
            value = computed_values[glyph.ttl]
            if value < .85:
                to_remove.add(glyph)
                x = glyph.pos[0] // (glyph_width + grid_spacing_x)
                y = glyph.pos[1] // (glyph_height + grid_spacing_y)
                try:
                    new = grid.layout[y + 1][x]
                    burn_glyph(new)
                except IndexError:
                    pass
            elif not glyph.image:
                to_remove.add(glyph)

        burn_set.difference_update(to_remove)

        current = len(burn_set)
        ratio = min(1, (float(current) / max_streamers / 2 ))
        if current < max_streamers and random() > ratio:
            glyph = choice(grid.layout[0])
            burn_glyph(glyph)

    def init_screen(width, height):
        return pygame.display.set_mode((width, height), pygame.RESIZABLE)

    def init_group(width, height):
        global logo
        global max_streamers

        burn_set.clear()

        cell_x = glyph_width + grid_spacing_x
        cell_y = glyph_height + grid_spacing_y
        cell_width = int(width // cell_x)
        cell_height = int(height // cell_y)

        max_streamers = int((cell_width * cell_height) / 10)

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
        clock.tick(60)

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
