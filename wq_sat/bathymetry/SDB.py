import numpy as np

## WQ_SAT
from wq_sat import config
from wq_sat.satellites import sentinel2

def wq_proxies(tile, coordinates=None):
    
    tile_path = config.acolite_path(tile)
    data_bands, coord = sentinel2.Rs_acolite(tile_path, coordinates)
    
    ## pZgrenn & pZred
    Zgreen = np.log(3140*data_bands['B2'])/np.log(3140*data_bands['B3'])
    Zred = np.log(3140*data_bands['B2'])/np.log(3140*data_bands['B4'])
    
    return Zgreen, Zred, data_bands['B2'], data_bands['B3'], data_bands['B5'], data_bands['chl'], coord

def composite_approach(tiles, coordinates=None):
    
    tile_path = config.acolite_path(tiles[0])
    data_bands, coord = sentinel2.Rs_acolite(tile_path, coordinates)
    h, w = data_bands['B2'].shape

    ## pZgrenn & pZred
    Zgreen = np.zeros((h, w, len(tiles)))
    Zred = np.zeros((h, w, len(tiles)))

    ## Water quality proxies
    Rs704 = np.zeros((h, w, len(tiles)))
    chl = np.zeros((h, w, len(tiles)))
    Rs492 = np.zeros((h, w, len(tiles)))
    Rs559 = np.zeros((h, w, len(tiles)))

    for t, tile in enumerate(tiles):

        tile_path = config.acolite_path(tile)
        data_bands, coord = sentinel2.Rs_acolite(tile_path, coordinates)

        ## Water quality proxies
        Rs492[:,:,t] = data_bands['B2']
        Rs559[:,:,t] = data_bands['B3']
        Rs704[:,:,t] = data_bands['B5']
        chl[:,:,t] = data_bands['chl']

        ## pZgrenn & pZred
        Zgreen[:,:,t] = np.log(3140*data_bands['B2'])/np.log(3140*data_bands['B3'])
        Zred[:,:,t] = np.log(3140*data_bands['B2'])/np.log(3140*data_bands['B4'])
        
    ## Max_pZgrenn and idx of Max_pZgrenn
    Zgr_max = np.nanmax(Zgreen, axis=2)
    idx_Zgr_max = Zgreen.argmax(axis=2)

    ## Max_pZred and idx of Max_pZred
    Zr_max = np.nanmax(Zred, axis=2)
    idx_Zr_max = Zred.argmax(axis=2)

    ## Composite of Water quality proxies
    m,n = idx_Zgr_max.shape
    i,j = np.ogrid[:m,:n]

    Rs492_c = Rs492[i, j, idx_Zgr_max] # Rs492 -> B2
    Rs559_c = Rs559[i, j, idx_Zgr_max] # Rs559 -> B3
    Rs704_c = Rs704[i, j, idx_Zgr_max] # Rs704 -> B5
    chl_c = chl[i, j, idx_Zgr_max] # chl
    
    return Zgr_max, Zr_max, Rs492_c, Rs559_c, Rs704_c, chl_c, coord

def switching_model(pSDBgreen, pSDBred, Zgr_coef = 3.5, Zr_coef = 2):

    # Equations
    a = (Zgr_coef - pSDBred)/ (Zgr_coef - Zr_coef)
    b = 1-a
    SDBw = a * pSDBred + b * pSDBgreen

    #create array
    SDB = np.zeros(pSDBred.shape)
    SDB[:,:] = np.nan

    # create a Switching SDB
    SDB = np.where(pSDBred < Zr_coef, pSDBred, SDB)
    SDB = np.where((pSDBred > Zr_coef) & (pSDBgreen > Zgr_coef), pSDBgreen, SDB)
    SDB = np.where((pSDBred >= Zr_coef) & (pSDBgreen <= Zgr_coef), SDBw, SDB)
    SDB[SDB < 0] = np.nan
    
    return SDB

def odw_model(SDB, Rs492, Rs559, Rs704):
    
    ## Clear waters
    SDB[Rs492 <= 0.003] = np.nan
    SDB[Rs559 <= 0.003] = np.nan
    
    ## Turbid waters
    Ymax = (-0.251 * np.log(Rs704)) + 0.8
    Ymax[Ymax < 0] = np.nan

    y = np.log(SDB)
    y[y < 0] = np.nan

    #eliminar valores por ecuacion paper 2019
    SDB[y > Ymax] = np.nan
    
    return SDB