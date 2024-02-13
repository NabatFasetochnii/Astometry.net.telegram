import aplpy
import astropy.io.fits as fits
from astropy import wcs
import numpy as np
from astropy.convolution import Gaussian2DKernel
from astropy.convolution import convolve
from astropy.stats import mad_std
from astroquery.astrometry_net import AstrometryNet
from photutils.detection import DAOStarFinder


def astrometry(path, comment):
    ast = AstrometryNet()
    ast.api_key = ''
    path2save = path.replace('.f', '.wcs.f')
    try:
        # read file, copy data and header
        with fits.open(path, mode='update', memmap=False) as hdulist:
            Header = hdulist[0].header
            try:
                buf = Header['CD1_1']
                gc = aplpy.FITSFigure(hdulist[0])
                gc.add_grid()
                gc.show_colorscale()
                gc.save(path + '.png')
                hdulist.close()
                return path, '', True
            except:
                pass
            Data = hdulist[0].data.copy()
            hdulist.verify('fix')
            hdulist.close()
            # gaussian convolution
            kernel = Gaussian2DKernel(x_stddev=1)
            Data = convolve(Data, kernel)
            # extract background
            Data -= np.median(Data)
            Bkg_sigma = mad_std(Data)
            # # mask bad row
            # mask = np.zeros(Data.shape, dtype=bool)
            # mask[90:110, 0:Data.shape[1]] = True
            daofind = DAOStarFinder(fwhm=4.5, threshold=5. * Bkg_sigma, sharplo=0.25)
            # Sources = daofind(Data, mask=mask)
            Sources = daofind(Data)
            # print(Sources.info)
            # plt.imshow(Data, cmap=cm.Greys_r, aspect='equal',
            #            norm=Normalize(vmin=-30, vmax=150), interpolation='nearest')
            # plt.scatter(Sources['xcentroid'], Sources['ycentroid'], s=40, facecolors='none', edgecolors='r')
            # plt.show()
            # Sort sources in ascending order
            Sources.sort('flux')
            Sources.reverse()
            # ast.show_allowed_settings()
            image_width = Header['NAXIS2']
            image_height = Header['NAXIS1']
            # print(Sources)
            if comment is not None:
                coms = comment.split(' ')
                wcs_header = ast.solve_from_source_list(Sources['xcentroid'],
                                                        Sources['ycentroid'],
                                                        image_width, image_height,
                                                        solve_timeout=120,
                                                        downsample_factor=2,
                                                        center_ra=coms[0],
                                                        center_dec=coms[1],
                                                        radius=coms[2],
                                                        scale_lower=coms[3],
                                                        scale_upper=coms[4],
                                                        scale_units='arcsecperpix'
                                                        )
            else:
                wcs_header = ast.solve_from_source_list(Sources['xcentroid'],
                                                        Sources['ycentroid'],
                                                        image_width, image_height,
                                                        solve_timeout=120,
                                                        downsample_factor=2
                                                        )
            hdulist[0].header = Header + wcs_header
            w = wcs.WCS(wcs_header)
            hdulist.writeto(path2save, overwrite=True)
            gc = aplpy.FITSFigure(path2save)
            gc.add_grid()
            gc.show_colorscale()
            gc.save(path2save + '.png')
            return path2save, w.__repr__(), False
    except Exception as e:
        print(e)
