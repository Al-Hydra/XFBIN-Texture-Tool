from array import array

from utils.PyBinaryReader.binary_reader import BinaryReader
from utils.xfbin_lib.xfbin import *
from utils.xfbin_lib.xfbin.structure.br.br_nut import *
from utils.xfbin_lib.xfbin.structure.nut import Nut, NutTexture
import copy
from dataclasses import dataclass

#read xfbin then store in a list    
xfbins = list()
binary_chunks = list()

def create_xfbin():
    xfbin = Xfbin()
    xfbin.add_chunk_page(NuccChunkNull())
    return xfbin

def read_xfbin(xfbin_path):
    try:
        xfbin = xfbin_reader.read_xfbin(xfbin_path)
    except:
        return None

    return xfbin

    

def write_xfbin(xfbin: Xfbin, xfbin_path):
    #reorder chunk pages so that texture are at the top
    xfbin.sort_pages_by_type(NuccChunkTexture)
    xfbin_writer.write_xfbin_to_path(xfbin, xfbin_path)



'''
class CopiedTextures:
    c_tex = list()
    def __init__(self, texture: NuccChunkTexture):
        self.name = texture.name
        self.filePath = texture.filePath
        self.nut = texture.nut

def create_texture_chunk(self):
    tex = NuccChunkTexture(CopiedTextures(self).filePath, CopiedTextures(self).name)
    tex_test = copy.deepcopy(tex)
    tex.has_props = True
    tex.nut = Nut()
    for attr in CopiedTextures(self).nut.__dict__:
        setattr(tex.nut, attr, getattr(CopiedTextures(self).nut, attr))
    CopiedTextures(self).c_tex.append(tex)
    return tex


def copy_texture(texture: NuccChunkTexture):
    tex = copy.deepcopy(texture)
'''
