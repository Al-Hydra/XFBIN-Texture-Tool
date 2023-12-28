from dds import NutTexture_to_DDS
from utils.PyBinaryReader.binary_reader import BinaryReader
from utils.xfbin_lib.xfbin import *
from utils.xfbin_lib.xfbin.structure.br.br_nut import *
from utils.xfbin_lib.xfbin.structure.nut import Nut, NutTexture

import os

#get current directory
path = os.getcwd()

#scan directories for .xfbin
def scan_xfbin(path):
    xfbin_paths = list()
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".xfbin"):
                xfbin_paths.append(os.path.join(root, file))
    return xfbin_paths

if __name__ == '__main__':
    list = scan_xfbin(path)

    input(f"Found {len(list)} xfbin files. Press enter to continue...")

    for xfpath in list:
        parent_dir = os.path.dirname(xfpath)
        try:
            xfbin = read_xfbin(xfpath)
            for page in xfbin.pages:
                for chunk in page.chunks:
                    if isinstance(chunk, NuccChunkTexture):
                        nut = chunk.nut
                        print(chunk.name)
                        for i in range(len(nut.textures)):
                            dds = NutTexture_to_DDS(nut.textures[i])
                            
                            with open(f'{parent_dir}//{chunk.name}_{i}.dds', 'wb') as f:
                                f.write(dds)
        except:
            print(f'Error reading {xfpath}')
            continue
    
    input("Done. Press enter to exit...")

