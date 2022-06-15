import json
import os

from pathlib import Path
from PIL import Image

lookup_table = [0] * 1024
palette = []


def load_rom(rom_file: str = './Zero Tolerance (USA, Europe).md') -> bytes:
    if Path(rom_file).is_file():
        with open(rom_file, 'rb') as rom:
            return rom.read()
    else:
        return b''


def load_palette(palette_file: str = 'palette.png') -> None:
    img = Image.open(palette_file)
    for x in range(img.width):
        palette.append(img.getpixel((x, 0)))


def load_texture_meta(meta_file: str = 'texture_meta.json') -> list:
    with open(meta_file, 'r') as json_file:
        meta = json_file.read()
        return json.loads(meta)


def init_lookup_table() -> None:
    for y in range(32):
        for x in range(32):
            lookup_table[(512 * (y % 2)) + (x % 2) + ((x // 2) * 32) + ((y // 2) * 2)] = x + y * 32


def get_pixel_data(data: bytes) -> list:
    # expand each byte to 2 bytes, assign colors from palette
    plist = [palette[(data[index // 2] >> 4)]
             if index % 2 == 0
             else
             palette[data[index // 2] & 0x0f]
             for index in range(1024)]

    # rearrange pixels into correct positions
    return [plist[p] for p in lookup_table]


def save_one_texture(offset: int) -> None:
    pixel_data = get_pixel_data(rom_data[offset:offset + 512])
    dst_image = Image.new('RGBA', (32, 32))
    dst_image.putdata(pixel_data)

    # todo replace with f string
    dst_image.save('./textures/texture_{0:08X}.png'.format(offset))


def save_many_textures(texture_meta: tuple) -> None:
    width = 16
    h_size = 32 * width

    if texture_meta[1] < width:
        h_size = 32 * texture_meta[1]
        width = texture_meta[1]

    v_size = 32 * ((texture_meta[1] + (width - 1)) // width)

    picture = Image.new(mode='RGBA', size=(h_size, v_size), color=palette[0])
    picture32 = Image.new(mode='RGBA', size=(32, 32), color=palette[0])

    for texture in range(texture_meta[1]):
        offset = texture_meta[0] + texture * 512
        pos = (texture % width) * 32, (texture // width) * 32

        picture32.putdata(get_pixel_data(rom_data[offset:offset + 512]))
        picture.paste(picture32, pos, picture32)

    picture.save('./textures/textures_0x{0:08X}.png'.format(texture_meta[0]))


def draw_meta_texture(offset: int, pos: tuple, picture: Image.Image):
    walltex_offset = 0x12EF26

    picture32 = Image.new(mode='RGBA', size=(32, 32), color=palette[0])

    for count in range(8):
        temp_x, temp_y = (count // 2) * 32, (count % 2) * 32

        ## Lazily reading the less significant byte of a big endian 2 byte number
        index = rom_data[offset + count * 2 + 1]
        temp_offset = walltex_offset + (index * 512)

        picture32.putdata(get_pixel_data(rom_data[temp_offset:temp_offset + 512]))
        picture.paste(picture32, (pos[0] + temp_x, pos[1] + temp_y), picture32)


def save_one_meta_texture(offset: int):
    picture = Image.new(mode='RGBA', size=(32 * 4, 32 * 2), color=palette[0])
    draw_meta_texture(offset, (0, 0), picture)
    picture.save('./textures/metatexture_0x{0:08X}.png'.format(offset))


def save_many_meta_textures(offset: int, count: int) -> None:
    width = 16
    h_size = 128 * width
    if count < width:
        h_size = 32 * count
        width = count

    v_size = 64 * ((count + (width - 1)) // width)

    picture = Image.new(mode='RGBA', size=(h_size, v_size), color=palette[0])

    for metaTexture in range(count):
        pos = (metaTexture % width) * 128, (metaTexture // width) * 64
        temp_offset = offset + metaTexture * 16
        draw_meta_texture(temp_offset, pos, picture)

    picture.save('./textures/metatextures_0x{0:08X}.png'.format(offset))


if __name__ == "__main__":
    rom_data = load_rom()

    if len(rom_data) != 0:
        load_palette()
        init_lookup_table()

        if not os.path.exists('./textures'):
            os.makedirs('./textures')

        textureTest_offset = 0x10E9BE
        save_one_texture(textureTest_offset)

        for t in load_texture_meta():
            save_many_textures(t)

        # wall textures
        save_many_textures((0x12EF26, 255))

        metatextureTest_offset = 0x15A52A
        save_one_meta_texture(metatextureTest_offset)

        metatextureOffsets = [0x15a10a, 0x160424, 0x16602c]

        for m in metatextureOffsets:
            save_many_meta_textures(m, 256)

    else:
        print("Error loading rom")
