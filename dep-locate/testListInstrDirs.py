'''
    Test module for the listInstrDirs module
    Uses the getDirList() function on a keyword
    and then prints the contents of the directories
    Precondition: Requires a valid instrument keyword
    Postcondition: Prints out the contents of the directories
        of the given instrument data disks
'''

import listInstrDirs as locate
import subprocess as sp

instruments = ['DEIMOS', 'ESI', 'HIRES', 'LRIS', 'MOSFIRE', 'NIRC2', 'NIRSPEC', 'OSIRIS', 'KCWI']

print("Enter an instrument keyword to search")
instr = input()

if instr in instruments:
    dirs = locate.getDirList('HIRES')

    for item in dirs:
        print(item)
        sp.run(['ls',item])
        print()
else:
    print("The key you entered does not exist")    
