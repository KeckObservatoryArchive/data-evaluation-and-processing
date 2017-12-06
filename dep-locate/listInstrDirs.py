'''
    Function to populate a list of data storage paths
    for a given instrument.
    Pre-condition: Must provide a valid instrument KEY
        Currently supported: DEIMOS, ESI, HIRES, LRIS, 
        MOSFIRE, NIRC2, NIRSPEC, OSIRIS, KCWI
    Post-condition: Returns a list of paths to data storage
        areas for the given instrument

    Written by Matthew Brown
    11/30/2017
'''

def getDirList(instr):
    # Create an empty directory list
    dirs = [] 

    # Initialize path variable to /s/sdata because all 
    # paths begin with that 
    path = '/s/sdata'

    # Look for the Keyword Supplied by the user
    if instr == 'DEIMOS':
        # add the disk numbers for the instrument
        path += '100'
        # DEIMOS has 3 disks associated with it
        for i in range(3):
            path2 = path + str(i+1)
            # add the account numbers
            for i in range(20):
                path3 =  path2 + '/deimos' + str(i+1)
                # Append the path to the directory list
                dirs.append(path3)
            # Add the engineering folder
            dirs.append(path2 + '/dmoseng')
        for i in range(7):
            if i != 4:
                path2 = path + str(i+1) + '/esi'
                for i in range(20):
                    path3 = path2 + str(i+1)
                    dirs.append(path3)
                dirs.append(path2 + 'eng')  
    elif instr == 'HIRES':
        path += '12'
        for i in range(3):
            path2 = path + str(i+5) + '/hires'
            for i in range(20):
                path3 = path2 + str(i+1)
                dirs.append(path3)
            dirs. append(path2 + 'eng')   
    elif instr == 'LRIS':
        path += '24'
        for i in range(3):
            path2 = path + str(i+1) + '/lris'
            for i in range(20):
                path3 = path2 + str(i+1)   
                dirs.append(path3)
            dirs.append(path2 + 'eng')    
    elif instr == 'MOSFIRE':
        path += '1300'    
        for i in range(9):
            path2 = path + '/mosfire' + str(i+1)   
            dirs.append(path2)
        dirs.append(path + '/moseng')    
        dirs.append(path + '/mosfire')
    elif instr == 'NIRC2':
        path += '90'
        for i in range(5):
            path2 = path + str(i) + '/nirc'
            for i in range(20):
                path3 = path2 + str(i+1)    
                dirs.append(path3)
        dirs.append(path2 + '2eng')
    elif instr == 'NIRSPEC':
        path += '60'
        for i in range(4):
            path2 = path + str(i) 
            for i in range(20):
                path3 = path2 + '/nspec' + str(i+1) 
                dirs.append(path3)
            dirs.append(path2 + '/nirspec')
            dirs.append(path2 + '/nspeceng')
    elif instr == 'OSIRIS':
        path += '110'    
        for i in range(2):
            path2 = path + str(i)
            for i in range(20):
                path3 = path2 + '/osiris'  + str(i+1)
                dirs.append(path3)
            dirs.append(path2 + '/osiriseng')
            dirs.append(path2 + 'osrseng')
            dirs.append(path2)
    elif instr == 'KCWI':
        path += '1400/kcwi'
        for i in range(9):
            path2 = path + str(i+1)
            dirs.append(path2)
        dirs.append(path + 'dev')
    elif instr == 'NIRES':
        path += '150'
        for i in range(3):
            path2 = path + str(i) + '/nireseng'
            dirs.append(path2)
    else: # If you get here, you put in a wrong instrument keyword
        logging.basicConfig(filename='debug.log', level=logging.DEBUG)
        logging.warning('dep_locate %s: Could not find instrument %s', instr, instr)
        print('dep_locate %s: Could not find instrument %s'.format(instr, instr))

    return dirs
