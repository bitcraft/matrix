"""  Matrix Screen Effect
    (c) 2016, Leif Theden, leif.theden@gmail.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
background = join('resources', 'python.png')
font_size = 32
screen_size = 640, 480
glyph_width = 14
glyph_height = 16
grid_spacing_x = 2
grid_spacing_y = 2
streamers = 0
computed_values = list()
layout = list()
glyphs = list()
burn_set = set()
max_streamers = 0
cache = list()
save_to_disk = 0
logo = None


class Glyph(object):
    pos = 0, 0
    ttl = 0
    index = 0


def calc_color(value):
    value *= 255.
    if value > 190:
        value1 = int(round(value))
        value2 = int((value * 255) / 300)
        return value2, value1, value2
    else:
        value1 = int((value * 255.) / 300.)
        value2 = int((value * 255) / 800)
        return value2, value1, value2


def burn_glyph(glyph):
    glyph.ttl = len(computed_values) - 1
    burn_set.add(glyph)


def update_burners():
    # go through the bright streamers
    old_set = burn_set.copy()
    to_remove = set()
    for glyph in old_set:
        value = computed_values[glyph.ttl]
        if value < .85:
            to_remove.add(glyph)
            x = glyph.pos[0] // (glyph_width + grid_spacing_x)
            y = glyph.pos[1] // (glyph_height + grid_spacing_y)
            try:
                new = layout[y + 1][x]
                burn_glyph(new)
            except IndexError:
                pass
        elif not glyph.ttl:
            to_remove.add(glyph)

    # remove the cells that are fading
    burn_set.difference_update(to_remove)

    # add new glyphs to make up for lost ones
    # using random in this way prevents horizontal lines
    current = len(burn_set)
    ratio = min(1, (float(current) / max_streamers / 2))
    if current < max_streamers and random() > ratio:
        glyph = choice(layout[0])
        burn_glyph(glyph)


def init_screen(width, height):
    global screen_size

    screen_size = width, height
    return pygame.display.set_mode(screen_size, pygame.RESIZABLE)


def init_grid(width, height):
    global max_streamers
    global glyphs
    global layout
    global logo

    logo = pygame.image.load(background).convert_alpha()
    logo = pygame.transform.smoothscale(logo, screen_size)
    cell_width = glyph_width + grid_spacing_x
    cell_height = glyph_height + grid_spacing_y
    grid_width = width // cell_width
    grid_height = height // cell_height
    max_streamers = int((grid_width * grid_height) / 10)

    layout = [[None] * grid_width for i in range(grid_height)]
    for y, x in product(range(grid_height), range(grid_width)):
        glyph = Glyph()
        glyph.ttl = randrange(len(computed_values))
        glyph.index = randrange(len(charset))
        glyph.pos = x * cell_width, y * cell_height
        layout[y][x] = glyph
    glyphs = [i for i in chain.from_iterable(layout)]


def generate_images(font):
    # generate a scanline image to create scanline effect
    scanline = pygame.Surface((glyph_width, glyph_height), pygame.SRCALPHA)
    for y in range(0, glyph_height, 2):
        pygame.draw.line(scanline, (0, 0, 0, 128), (0, y), (glyph_width, y))

    # render all characters a head of time
    for char in charset:
        chars = list()
        cache.append(chars)
        for value in computed_values:
            color = calc_color(value)
            temp = font.render(char, 1, color)
            temp = pygame.transform.smoothscale(temp, (glyph_width, glyph_height))
            temp.blit(scanline, (0, 0))
            image = pygame.Surface(temp.get_size())
            image.blit(temp, (0, 0))
            chars.append(image)


def compute_curve():
    # compute the color curve for the streamers
    time = 0.
    duration = 5000.
    prog = 0
    while prog < 1:
        prog = min(1., time / duration)
        p = prog - 1.0
        value = 1. - sqrt(1.0 - p * p)
        computed_values.insert(0, value)
        time += 16


def main():
    pygame.init()
    pygame.font.init()

    screen = init_screen(*screen_size)
    font = pygame.font.Font(font_name, font_size)
    clock = pygame.time.Clock()

    compute_curve()
    generate_images(font)
    init_grid(*screen_size)

    frame_number = 0
    running = True
    while running:
        if not save_to_disk:
            clock.tick()
            print(clock.get_fps())

        for event in pygame.event.get():
            if event.type == pygame.VIDEORESIZE:
                if not screen_size == (event.w, event.h):
                    screen = init_screen(event.w, event.h)
                    init_grid(event.w, event.h)
                    burn_set.clear()

            elif event.type == pygame.QUIT:
                running = False

        update_burners()

        # update and draw grid to the screen
        screen_blit = screen.blit
        for glyph in (i for i in glyphs if i.ttl):
            # have random chance to change the glyph
            if random() > .9:
                glyph.index = randrange(len(charset))

            # update the glyphs's life and image
            # if it becomes 0, then it won't be updated next frame
            glyph.ttl -= 1

            # get image and draw it
            screen_blit(cache[glyph.index][glyph.ttl], glyph.pos)

        screen_blit(logo, (0, 0), None, pygame.BLEND_RGBA_MULT)

        if save_to_disk:
            filename = "snapshot%05d.tga" % frame_number
            pygame.image.save(screen, filename)
            frame_number += 1

        else:
            pygame.display.flip()


if __name__ == "__main__":
    main()
