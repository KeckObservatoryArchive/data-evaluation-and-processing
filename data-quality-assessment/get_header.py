from astropy.io import fits

class HDU():
	def __init__(self, file):
		self.data = fits.getdata(file)
		self.keywords = fits.getheader(file)
		
		# all common keywords
		self.instr = self.keywords['INSTRUME']
		self.ra = self.keywords['RA']
		self.dec = self.keywords['DEC']
		self.naxis1 = self.keywords['NAXIS1']
		self.naxis2 = self.keywords['NAXIS2']
		self.binning = self.keywords['BINNING']

	# instrument specific kewywords
	def kcwi(self):
		self.camera = self.keywords['CAMERA']
		self.parantel = self.keywords['PARATEL']
		self.parang = self.keywords['PARANG']

	def nirspec(self):
		pass

	def hires(self):
		pass


