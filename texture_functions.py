import copy
#from utils.PyBinaryReader.binary_reader import BinaryReader
from utils.xfbin_lib.xfbin import *
#from utils.xfbin_lib.xfbin.structure.br.br_nut import *
from utils.xfbin_lib.xfbin.structure.nut import Nut, NutTexture
from zlib import crc32
from dataclasses import dataclass
from array import array
from PIL import Image
import io
from dds import *

@dataclass
class PNG(BrStruct):
    def __init__(self):
        self.Signature = b'\x89PNG\r\n\x1a\n'
        self.Chunks = []

    def __br_read__(self, br: BinaryReader, *args):
        self.Signature = br.read_bytes(8)
        while not br.eof():
            self.Chunks.append(br.read_struct(PNG_Chunk))

    def __br_write__(self, br: BinaryReader, *args):
        br.write_bytes(self.Signature)
        for chunk in self.Chunks:
            br.write_struct(chunk)


class PNG_Chunk(BrStruct):
    def __init__(self):
        self.Length = 0
        self.Type = 0
        self.Data = None
        self.CRC = 0

    def __br_read__(self, br: BinaryReader, *args):
        self.Length = br.read_uint32()
        self.Type = br.read_str(4)

        #read the correct struct based on the type
        #self.Data = br.read_struct(globals()[self.Type], None, self.Length)
        self.Data = br.read_bytes(self.Length)

        self.CRC = br.read_uint32()

    def __br_write__(self, br: BinaryReader, *args):

        #write the chunk data first to get its size
        datbr = BinaryReader(bytearray(), Endian.BIG)
        datbr.write_str(self.Type)
        datbr.write_struct(self.Data)

        br.write_uint32(datbr.size() - 4)

        br.extend(datbr.buffer())
        br.seek(datbr.size(), 1)

        br.write_uint32(crc32(datbr.buffer()))


class IHDR(PNG_Chunk):
    def __init__(self):
        self.Width = 0
        self.Height = 0
        self.BitDepth = 0
        self.ColorType = 0
        self.CompressionMethod = 0
        self.FilterMethod = 0
        self.InterlaceMethod = 0

    def __br_read__(self, br: BinaryReader, *args):
        self.Width = br.read_uint32()
        self.Height = br.read_uint32()
        self.BitDepth = br.read_uint8()
        self.ColorType = br.read_uint8()
        self.CompressionMethod = br.read_uint8()
        self.FilterMethod = br.read_uint8()
        self.InterlaceMethod = br.read_uint8()

    def __br_write__(self, br: BinaryReader, *args):
        br.write_uint32(self.Width)
        br.write_uint32(self.Height)
        br.write_uint8(self.BitDepth)
        br.write_uint8(self.ColorType)
        br.write_uint8(self.CompressionMethod)
        br.write_uint8(self.FilterMethod)
        br.write_uint8(self.InterlaceMethod)

nut_pf_fourcc = {
    'DXT1': 0,
    'DXT3': 1,
    'DXT5': 2,
}

nut_pf_bitmasks = {
    (0xf800, 0x7e0, 0x1f, 0): 8,
    (0x7c00, 0x3e0, 0x1f, 0x8000): 6,
    (0x0f00, 0x00f0, 0x000f, 0xf000): 7,
    (0x00ff0000, 0x0000ff00, 0x000000ff, 0x0): 14,
    (0x00ff0000, 0x0000ff00, 0x000000ff, 0xff000000): 17,
}

nut_bpp = {
    8: 2,
    6: 2,
    7: 2,
    14: 4,
    17: 4,
}

def read_dds_path(path):
    with open(path, 'rb') as f:
        file = f.read()

    with BinaryReader(file, Endian.LITTLE) as br:
        dds: DDS = br.read_struct(DDS)
    return dds

def read_dds(file):
    with BinaryReader(file, Endian.LITTLE) as br:
        dds: DDS = br.read_struct(DDS)
    return dds


def texture_565(texture_data, width, height):
    texture_data = array('u', texture_data)
    texture_data.byteswap()

    return Image.frombytes('RGB', (width, height), texture_data.tobytes(), 'raw', 'BGR;16')


def texture_5551(texture_data, width, height):
    texture_data = array('u', texture_data)
    texture_data.byteswap()

    return Image.frombytes('RGBA', (width, height), texture_data.tobytes(), 'raw', 'BGRA;15')


def texture_4444(texture_data, width, height):
    texture_data = array('u', texture_data)
    texture_data.byteswap()

    image = Image.frombytes('RGBA', (width, height),
                            texture_data.tobytes(), 'raw', 'RGBA;4B')
    r, g, b, a = image.split()
    return Image.merge('RGBA', (b, g, r, a))


def texture_8888(texture_data, width, height):
    image = Image.frombytes('RGBA', (width, height), texture_data, 'raw')
    r, g, b, a = image.split()
    return Image.merge('RGBA', (g, b, a, r))

textures = list()
CopiedTextures = list()

@dataclass
class Texture:
    name: str
    filePath: str
    type: str
    data: array
    def __init__(self):
        self.name = ""
        self.filePath = ""
        self.width = None
        self.height = None
        self.type = None
        self.pixel_format = None
        self.mipmap_count = None
        self.data = None
        self.chunk = None
    

def DDS_to_NutTexture(dds):
    dds: DDS
    nut = NutTexture()

    nut.width = dds.header.width
    nut.height = dds.header.height

    if dds.header.pixel_format.fourCC != '':
        nut.pixel_format = nut_pf_fourcc[dds.header.pixel_format.fourCC]
        nut.mipmaps = list()
        nut.texture_data = b''
        for mip in dds.mipmaps:
            if len(mip) < 16:
                mip += b'\x00' * (16 - len(mip))
            print(len(mip))
            nut.mipmaps.append(mip)
            nut.texture_data += mip
    elif dds.header.pixel_format.bitmasks:
        nut.pixel_format = nut_pf_bitmasks[dds.header.pixel_format.bitmasks]
        nut.mipmaps = list()
        nut.texture_data = b''

        if nut.pixel_format == 17:
            for mip in dds.mipmaps:
                mip = array('l', mip)
                mip.byteswap()
                nut.mipmaps.append(mip.tobytes())
                nut.texture_data += mip.tobytes()

        else:
            for mip in dds.mipmaps:
                if len(mip) < 16:
                    mip += b'\x00' * (16 - len(mip))
                mip = array('u', mip)
                mip.byteswap()
                nut.mipmaps.append(mip.tobytes())
                nut.texture_data += mip.tobytes()

    nut.mipmap_count = dds.header.mipMapCount

    nut.is_cube_map = False
    nut.cubemap_format = 0

    nut.data_size = len(nut.texture_data)
    nut.header_size = 48

    if dds.header.mipMapCount > 1:
        nut.header_size += (dds.header.mipMapCount * 4)
    else:
        nut.header_size = 48
    
    if nut.header_size % 0x08 != 0:
        nut.header_size += nut.header_size % 0x08

    nut.header_size += 32

    nut.total_size = nut.data_size + nut.header_size

    return nut


def NutTexture_to_DDS(nuttex: NutTexture):
    dds = DDS()
    dds.magic = 'DDS '
    header = dds.header = DDS_Header()
    header.pixel_format = DDS_PixelFormat()
    header.size = 124
    # DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT
    header.flags = 0x1 | 0x2 | 0x4 | 0x1000

    header.width = nuttex.width
    header.height = nuttex.height
    header.mipMapCount = nuttex.mipmap_count

    # check if nuttex.pixel_format is in nut_pf_fourcc
    if nuttex.pixel_format in nut_pf_fourcc.values():

        header.pixel_format.fourCC = list(nut_pf_fourcc.keys())[list(
            nut_pf_fourcc.values()).index(nuttex.pixel_format)]
        header.flags |= 0x80000  # LINEAR_SIZE
        header.pixel_format.flags = 0x4  # DDPF_FOURCC

        if header.pixel_format.fourCC == 'DXT1':
            header.pitchOrLinearSize = nuttex.width * nuttex.height // 2
        else:
            header.pitchOrLinearSize = nuttex.width * nuttex.height

        header.pixel_format.rgbBitCount = 0
        header.pixel_format.bitmasks = (0, 0, 0, 0)

        dds.mipmaps = nuttex.mipmaps
        dds.texture_data = nuttex.texture_data

    elif nuttex.pixel_format in nut_pf_bitmasks.values():
        header.flags |= 0x8  # DDSD_PITCH
        header.pitchOrLinearSize = nuttex.width * nut_bpp[nuttex.pixel_format]
        header.pixel_format.fourCC = None
        header.pixel_format.rgbBitCount = nut_bpp[nuttex.pixel_format] * 8
        header.pixel_format.bitmasks = list(nut_pf_bitmasks.keys())[list(
            nut_pf_bitmasks.values()).index(nuttex.pixel_format)]
        if nuttex.pixel_format in (6, 7, 17):
            header.pixel_format.flags = 0x40 | 0x01  # DDPF_RGB | DDPF_ALPHAPIXELS
        else:
            header.pixel_format.flags = 0x40  # DDPF_RGB

        if nuttex.pixel_format in (6, 7, 8):
            dds.mipmaps = nuttex.mipmaps
            texture_data = array('u', nuttex.texture_data)
            texture_data.byteswap()
            dds.texture_data = texture_data.tobytes()
        elif nuttex.pixel_format in (14, 17):
            dds.mipmaps = nuttex.mipmaps
            texture_data = array('l', nuttex.texture_data)
            texture_data.byteswap()
            dds.texture_data = texture_data.tobytes()

    header.pixel_format.size = 32
    if header.mipMapCount > 1:
        header.flags |= 0x20000  # DDSD_MIPMAPCOUNT
        header.caps1 = 0x8 | 0x1000 | 0x400000
    else:
        header.caps1 = 0x8
    header.depth = 1
    header.reserved = [0] * 11
    header.caps2 = 0
    header.caps3 = 0
    header.caps4 = 0
    header.reserved2 = 0

    br = BinaryReader(endianness=Endian.LITTLE)
    br.write_struct(DDS(), dds)
    return br.buffer()

def write_dds(texture, path):
    for i, tex in enumerate(texture.data.textures):
        save = f'{path}/{texture.name}_{i}.dds'
        print(f'Writing {save}')
        with open(save, 'wb') as f:
            f.write(NutTexture_to_DDS(tex))
        f.close()


def NutTexture_to_PNG(texture: Texture, path):
    for i, tex in enumerate(texture.data.textures):
        save = f'{path}/{texture.name}_{i}.png'
        print(f'Writing {save}')
        if tex.pixel_format == 0 or tex.pixel_format == 1 or tex.pixel_format == 2:
            dxt1 = NutTexture_to_DDS(tex)
            img = Image.open(io.BytesIO(dxt1)).save(save, 'PNG')
        elif tex.pixel_format == 6:
            texture_5551(tex.texture_data, tex.width,
                         tex.height).save(save, 'PNG')
        elif tex.pixel_format == 7:
            texture_4444(tex.texture_data, tex.width,
                         tex.height).save(save, 'PNG')
        elif tex.pixel_format == 8:
            texture_565(tex.texture_data, tex.width,
                        tex.height).save(save, 'PNG')
        elif tex.pixel_format == 14 or tex.pixel_format == 17:
            texture_8888(tex.texture_data, tex.width,
                         tex.height).save(save, 'PNG')


def copy_texture(texture: NuccChunkTexture):
    tex = copy.deepcopy(texture)
    return tex


def get_textures(xfbin: Xfbin):
    filtered_chunks = list()
    for page in xfbin.pages:
        for chunk in page.chunks:
            if chunk.filePath.endswith('.nut'):
                tex = Texture()
                tex.name = chunk.name
                tex.filePath = chunk.filePath
                tex.chunk = chunk
                tex.type = 'nut'
                tex.data = chunk.nut

                filtered_chunks.append(tex)
            elif chunk.filePath.endswith('.png') or chunk.filePath.endswith('.dds'):
                br = BinaryReader(chunk.binary_data, endianness=Endian.BIG, encoding='cp932')
                tex = Texture()
                tex.name = chunk.name
                tex.filePath = chunk.filePath
                tex.chunk = chunk

                magic = br.read_bytes(4)
                if magic == b'DDS ':
                    tex.type = 'dds'
                    br.seek(-4, 1)
                    tex.data = chunk.binary_data
                    with BinaryReader(tex.data, Endian.LITTLE) as brdds:
                        
                        dds: DDS = brdds.read_struct(DDS)
                    tex.width = dds.header.width
                    tex.height = dds.header.height
                    tex.pixel_format = dds.header.pixel_format.fourCC
                    tex.mipmap_count = dds.header.mipMapCount


                elif magic == b'\x89PNG':
                    tex.type = 'png'
                    br.seek(-4, 1)
                    tex.data = chunk.binary_data
                    png = PNG()
                    png.__br_read__(BinaryReader(tex.data, endianness=Endian.BIG, encoding='cp932'))
                    ihdr = BinaryReader(png.Chunks[0].Data, endianness=Endian.BIG, encoding='cp932')
                    ihdr = ihdr.read_struct(IHDR)
                    tex.width = ihdr.Width
                    tex.height = ihdr.Height
                    tex.pixel_format = ihdr.ColorType
                    tex.mipmap_count = 1


                filtered_chunks.append(tex)
    return filtered_chunks

def create_texture_chunk(texture: Texture):
    tex = NuccChunkTexture(texture.filePath, texture.name)
    tex.has_props = True
    tex.nut = texture.data
    return tex

def create_binary_chunk(texture: Texture):
    tex = NuccChunkBinary(texture.filePath, texture.name)
    tex.has_props = True
    tex.binary_data = texture.data
    return tex

if __name__ == '__main__':
    path = r"C:\Users\Ali\Documents\GitHub\nut-tools\dist\adv_exam_brt_I1.dds"
    with open(path, 'rb') as f:
        data = f.read()
    with BinaryReader(data, Endian.BIG) as br:
        dds: DDS = br.read_struct(DDS)
    print(dds.header.pixel_format.fourCC)


def check_texture(path):
    with open(path, 'rb') as f:
        data = f.read()
    
    if data[:4] == b'DDS ':
        return 'dds'
    elif data[:4] == b'\x89PNG':
        return 'png'
    else:
        #try reading as nut
        with BinaryReader(data, Endian.BIG) as br:
            nut: Nut = br.read_struct(Nut)
            if nut.magic == "NTP3":
                return 'nut'
            else:
                return None


def nuttex_to_nut(nuttex: NutTexture):
    nut = Nut()
    
    nut.textures = [nuttex]
    return nut


def nut_to_texture(nut: Nut, name):
    #tex = NuccChunkTexture(f'c/chr/tex/{name}.nut', f'{name}')
    tex = Texture()
    tex.name = name
    tex.filePath = f'{name}.nut'
    tex.has_props = True
    tex.data = nut
    tex.height = nut.textures[0].height
    tex.width = nut.textures[0].width
    tex.pixel_format = nut.textures[0].pixel_format
    tex.mipmap_count = nut.textures[0].mipmap_count


    return tex

def read_nut(path, name):
    with open(path, 'rb') as f:
        data = f.read()
    with BinaryReader(data, Endian.BIG) as br:
        nut: BrNut = br.read_struct(BrNut)

    tex = nut_to_texture(nut, name)

    return tex

def write_nut(texture, nut_path):
    nut_path = f'{nut_path}//{texture.name}.nut'
    nut: Nut = texture.data
    br = BinaryReader(endianness=Endian.BIG)
    br.write_struct(BrNut(), nut)
    with open(nut_path, 'wb') as f:
        f.write(br.buffer())
    print(f'Wrote {nut_path}')


def dds_to_texture(dds: DDS, name):
    tex = Texture()
    tex.name = name
    tex.filePath = f'{name}.dds'
    tex.type = 'dds'
    tex.data = dds
    dds: DDS = BinaryReader(tex.data, Endian.LITTLE).read_struct(DDS)
    tex.width = dds.header.width
    tex.height = dds.header.height
    tex.pixel_format = dds.header.pixel_format.fourCC
    tex.mipmap_count = dds.header.mipMapCount
    return tex


def read_png(path):
    with open(path, 'rb') as f:
        data = f.read()
    with BinaryReader(data, Endian.BIG) as br:
        png: PNG = br.read_struct(PNG)
    return png    


def png_to_texture(png: PNG, name):
    tex = Texture()
    tex.name = name
    tex.filePath = f'{name}.png'
    tex.type = 'png'
    tex.data = png
    png: PNG = BinaryReader(tex.data, Endian.BIG, encoding='cp932').read_struct(PNG)
    ihdr = BinaryReader(png.Chunks[0].Data, endianness=Endian.BIG, encoding='cp932').read_struct(IHDR)

    tex.width = ihdr.Width
    tex.height = ihdr.Height
    tex.pixel_format = ihdr.ColorType
    tex.mipmap_count = 1

    return tex