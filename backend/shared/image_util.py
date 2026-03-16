import zlib

def tohash(imgpath):
    with open(imgpath,"rb") as f:
        return zlib.adler32(f.read())