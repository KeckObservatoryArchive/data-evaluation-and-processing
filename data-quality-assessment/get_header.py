from astropy.io import fits

class HDU():
	def __init__(self, file):
		self.hdu = fits.open(file)
		self.keywords = self.hdu[0].header
		self.data = self.hdu[0].data



