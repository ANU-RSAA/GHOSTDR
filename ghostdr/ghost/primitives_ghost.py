#
#                                                                  gemini_python
#
#                                                            primitives_ghost.py
# ------------------------------------------------------------------------------
from geminidr.gemini.primitives_gemini import Gemini
from geminidr.core.primitives_ccd import CCD
from .primitives_calibdb_ghost import CalibDBGHOST

from .parameters_ghost import ParametersGHOST

from .lookups import timestamp_keywords as ghost_stamps

from recipe_system.utils.decorators import parameter_override
# ------------------------------------------------------------------------------
_HDR_SIZE_REGEX = re.compile(r'^\[(?P<x1>[0-9]*)\:'
                             r'(?P<x2>[0-9]*),'
                             r'(?P<y1>[0-9]*)\:'
                             r'(?P<y2>[0-9]*)\]$')


def filename_updater(ad, **kwargs):
    origname = ad.filename
    ad.update_filename(**kwargs)
    rv = ad.filename
    ad.filename = origname
    return rv


@parameter_override
class GHOST(Gemini, CCD, CalibDBGHOST):
    """
    This is the class containing all of the calibration bookkeeping primitives
    for the GHOST level of the type hierarchy tree. It inherits all
    the primitives from the level above
    """
    tagset = set()  # Cannot be assigned as a class

    def __init__(self, adinputs, **kwargs):
        super(GHOST, self).__init__(adinputs, **kwargs)
        self.inst_lookups = 'ghostdr.ghost.lookups'
        self.parameters = ParametersGHOST
        # Add GHOST-specific timestamp keywords
        self.timestamp_keys.update(ghost_stamps.timestamp_keys)

    def _rebin_ghost_ad(self, ad, xb, yb):
        """
        Internal helper function to re-bin GHOST data.

        .. note::
            This function is *not* a primitive. It is designed to be called
            internally by public primitives.

        This function should be used for all re-binning procedures on
        AstroData objects that will be saved during reduction. It is designed
        to handle the correct adjustment of the relevant header keywords.

        This function has been included within the GHOST primitive class
        mostly so logging is consistent. Otherwise, it could be defined as
        a @staticmethod (or just exist outside the class completely).

        Parameters
        ----------
        ad : :any:`astrodata.AstroData` object
        xb : :obj:`int`
            x-binning
        yb : :obj:`int`
            y-binning

        Returns
        -------
        ad : :any:`astrodata.AstroData` object
            Input AstroData object, re-binned to the requested format
        """
        log = self.log

        # Input checking
        xb = int(xb)
        yb = int(yb)
        if not isinstance(ad, astrodata.AstroData):
            raise ValueError('ad is not a valid AstroData instance')
        for ext in ad:
            if ext.hdr.get('CCDSUM') != '1 1':
                raise ValueError(
                    'Cannot re-bin data that has already been binned')

        # Re-binning
        log.stdinfo('Re-binning %s' % ad.filename)
        rows = xb
        cols = yb
        for ext in ad:
            # Do the re-binning
            binned_array = ext.data.reshape(
                int(ext.data.shape[0] / rows), rows,
                int(ext.data.shape[1] / cols), cols
            ).sum(axis=1).sum(axis=2)
            ext.data = binned_array
            # Update header values
            ext.hdr.set('CCDSUM',
                        value='%d %d' % (rows, cols,),
                        comment='Re-binned to %dx%d' % (rows, cols,))

            old_datasec = ext.hdr.get('DATASEC')
            if old_datasec:
                datasec_values = _HDR_SIZE_REGEX.match(old_datasec)
                ext.hdr.set('DATASEC',
                            value='[%d:%d,%d:%d]' %
                                  (max(int(datasec_values.group('x1')) / xb, 1),
                                   max(int(datasec_values.group('x2')) / xb, 1),
                                   max(int(datasec_values.group('y1')) / yb, 1),
                                   max(int(datasec_values.group('y2')) / yb, 1),
                                   ),
                            comment='Re-binned to %dx%d' % (rows, cols,)
                            )
            old_trimsec = ext.hdr.get('TRIMSEC')
            if old_trimsec:
                ext.hdr.set('TRIMSEC',
                            value='[%d:%d,%d:%d]' %
                                  (max(int(datasec_values.group('x1')) / xb, 1),
                                   max(int(datasec_values.group('x2')) / xb, 1),
                                   max(int(datasec_values.group('y1')) / yb, 1),
                                   max(int(datasec_values.group('y2')) / yb, 1),
                                   ),
                            comment='Re-binned to %dx%d' % (rows, cols,)
                            )

            old_ampsize = ext.hdr.get('AMPSIZE')
            if old_ampsize:
                ampsize_values = _HDR_SIZE_REGEX.match(old_datasec)
                ext.hdr.set('AMPSIZE',
                            value='[%d:%d,%d:%d]' %
                                  (max(int(ampsize_values.group('x1')) / xb, 1),
                                   max(int(ampsize_values.group('x2')) / xb, 1),
                                   max(int(ampsize_values.group('y1')) / yb, 1),
                                   max(int(ampsize_values.group('y2')) / yb, 1),
                                   ),
                            comment='Re-binned to %dx%d' % (rows, cols,)
                            )

        return ad
