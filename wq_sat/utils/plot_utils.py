import numpy as np

def get_RGBimage(Rband, Gband, Bband):
    
    if not (Rband.shape == Gband.shape) or not (Rband.shape == Bband.shape):
        raise ValueError('Invalid RGB Bands. The bands are not the same size!!')
    
    Rband = np.clip(Rband, np.percentile(Rband, 2.5), np.percentile(Rband, 97.5))
    Gband = np.clip(Gband, np.percentile(Gband, 2.5), np.percentile(Gband, 97.5))
    Bband = np.clip(Bband, np.percentile(Bband, 2.5), np.percentile(Bband, 97.5))

    im = np.array([Rband, Gband, Bband])
    im = im * 255 / np.amax(im)
    im = np.moveaxis(im, 0, -1)

    return im.astype('uint8')