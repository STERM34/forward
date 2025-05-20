def what(file, h=None):

    if h is None:
        if isinstance(file, str):
            with open(file, 'rb') as f:
                h = f.read(32)
        else:
            location = file.tell()
            h = file.read(32)
            file.seek(location)
    
    if h.startswith(b'\xff\xd8'):
        return 'jpeg'
    elif h.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    elif h.startswith(b'GIF87a') or h.startswith(b'GIF89a'):
        return 'gif'
    elif h.startswith(b'BM'):
        return 'bmp'
    elif h.startswith(b'RIFF') and h[8:12] == b'WEBP':
        return 'webp'
    return None

def test_jpeg(h, f):
    if h.startswith(b'\xff\xd8'):
        return 'jpeg'
    return None

def test_png(h, f):
    if h.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    return None

def test_gif(h, f):
    if h.startswith(b'GIF87a') or h.startswith(b'GIF89a'):
        return 'gif'
    return None

def test_bmp(h, f):
    if h.startswith(b'BM'):
        return 'bmp'
    return None

def test_webp(h, f):
    if h.startswith(b'RIFF') and h[8:12] == b'WEBP':
        return 'webp'
    return None

tests = [
    test_jpeg,
    test_png,
    test_gif,
    test_bmp,
    test_webp
] 