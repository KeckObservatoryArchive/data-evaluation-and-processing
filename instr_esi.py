'''
This is the class to handle all the ESI specific attributes
ESI specific DR techniques can be added to it in the future

12/14/2017 M. Brown - Created initial file
'''

import instrument

class Esi(instrument.Instrument):
    def __init__(self, instr, utDate, rootDir, log=None):
        # Call the parent init to get all the shared variables
        super().__init__(instr, utDate, rootDir, log)

        # Other vars that subclass can overwrite
        self.endTime = '20:00:00'   # 24 hour period start/end time (UT)

        # Set the esi specific paths to anc and stage
        seq = (self.rootDir,'/ESI/', self.utDate, '/anc')
        self.ancDir = ''.join(seq)
        seq = (self.rootDir, '/stage')
        self.stageDir = ''.join(seq)
        # Generate the paths to the ESI datadisk accounts
        self.paths = self.get_dir_list()


    def get_dir_list(self):
        '''
        Function to generate the paths to all the ESI accounts, including engineering
        Returns the list of paths
        '''
        dirs = []
        path = '/s/sdata70'
        for i in range(8):
            if i != 5:
                joinSeq = (path, str(i), '/esi')
                path2 = ''.join(joinSeq)
                for j in range(1,21):
                    joinSeq = (path2, str(j))
                    path3 = ''.join(joinSeq)
                    dirs.append(path3)
                joinSeq = (path2, 'eng')
                path3 = ''.join(joinSeq)
                dirs.append(path3)
        return dirs

    def get_prefix(self, keys):
        instr = self.get_prefix(keys)
        if instr == 'esi':
            prefix = 'EI'
        else:
            prefix = ''
        return prefix

    def set_koaimtyp(self):
        """
        Uses get_koaimtyp to set KOAIMTYP
        """

        self.log.info('set_koaimtyp: setting KOAIMTYP keyword value')

        koaimtyp = self.get_koaimtyp(self)

        # Warn if undefined
        if koaimtyp == 'undefined':
            self.log.warning('set_koaimtyp: Could not determine KOAIMTYP value')

        # Update keyword
        self.set_keyword('KOAIMTYP', koaimtyp, 'KOA: Image type')

        return True

    def get_koaimtyp(self):
        """
        Determine iamge type based on instrument keyword configuration
        """

        # Default KOAIMTYP value
        koaimtyp = 'undefined'

        # Check OBSTYPE first
        obstype = self.get_keyword('OBSTYPE').lower()

        if obstype == 'bias': return 'bias'
        if obstype == 'dark': return 'dark'

        slmsknam = self.get_keyword('SLMSKNAM').lower()
        hatchpos = self.get_keyword('HATCHPOS').lower()
        lampqtz1 = self.get_keyword('LAMPQTZ1').lower()
        lampar1 = self.get_keyword('LAMPAR1').lower()
        lampcu1 = self.get_keyword('LAMPCU1').lower()
        lampne1 = self.get_keyword('LAMPNE1').lower()
        lampne2 = self.get_keyword('LAMPNE2').lower()
        prismnam = self.get_keyword('PRISMNAM').lower()
        imfltnam = self.get_keyword('IMFLTNAM').lower()
        idfltnam = self.get_keyword('IDFLTNAM').lower()
        axestat = self.get_keyword('AXESTAT').lower()
        domestat = self.get_keyword('DOMESTAT').lower()
        el = self.get_keyword('EL').lower()
        dwfilnam = self.get_keyword('DWFILNAM').lower()

        # Hatch
        hatchOpen = 1
        if hatchpos == 'closed': hatchOpen = 0

        # Is flat lamp on?
        flat = 0
        if lampqtz1 == 'on': flat = 1

        # Is telescope pointed at flat screen?
        flatPos = 0
        if el >= 44.0 and el <= 46.01: flatPos = 1

        # Is an arc lamp on?
        arc = 0
        if lampar1 == 'on' or lampcu1 == 'on' or lampne1 == 'on' or lampne2 == 'on':
            arc = 1

        # Dome/Axes tracking
        axeTracking = domeTracking = 1
        if axestat == 'not tracking': axeTracking = 0
        if domestat == 'not tracking': domeTracking = 0

        # This is a trace or focus
        if 'hole' in slmsknam:
            if not hatchOpen:
                if flat and not arc and prismnam == 'in' and imfltnam == 'out': return 'trace'
                if flat and not arc and prismnam != 'in' and imfltnam != 'out': return 'focus'
                if not flat and arc and prismnam == 'in' and imfltnam == 'out': return 'focus'
            else:
                if prismnam == 'in' and imfltnam == 'out':
                    if obstype == 'dmflat' and not domeTracking and flatPos: return 'trace'
                    if not axeTracking and not domeTracking and flatPos: return 'trace'
                    if obstype == 'dmflat' and not axeTracking and not domeTracking and flatPos: return 'trace'
                    if obstype == 'dmflat' and not axeTracking and flatPos: return 'trace'
                else:
                    if obstype == 'dmflat' and not domeTracking and flatPos: return 'focus'
                    if not axeTracking and not domeTracking and flatPos: return 'focus'
                    if obstype == 'dmflat' and not axeTracking and not domeTracking and flatPos: return 'focus'
                    if obstype == 'dmflat' and not axeTracking and flatPos: return 'focus'
            if prismnam == 'out' and infltnam == 'in' and ldfltnam == 'out': return 'focus'
            if prismnam == 'in' and infltnam == 'out' and dwfilnam == 'clear_s': return 'focus'
        else:
            if not hatchOpen:
                if flat and not arc: return 'flatlamp'
                if not flat and arc and prismnam == 'in' and imfltnam == 'out': return 'arclamp'
            else:
                if obstype == 'dmflat' and not domeTracking and flatPos: return 'flatlamp'
                if not axeTracking and not domeTracking and flatPos: return 'flatlamp'
                if obstype == 'dmflat' and not axeTracking and not domeTracking: return 'flatlamp'
                if obstype == 'dmflat' and not axeTracking and flatPos: return 'flatlamp'
                if not lamp and not arc: return 'object'

        return 'undefined'
