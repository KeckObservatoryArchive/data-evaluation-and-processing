from astropy.io import fits

class HDU():
	def __init__(self, filename):
		self.hdu = fits.open(filename)
		self.keywords = self.hdu[0].header
		self.data = self.hdu[0].data



