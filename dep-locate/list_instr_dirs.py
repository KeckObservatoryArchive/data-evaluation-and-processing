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

def getDirList(instr, log_writer):
    '''
    This function takes an instrument and generates all the storage locations of that instrument

    @type instr: string
    @param instr: The keyword for the instrument being examined
    @type log_writer: Logger Object
    @param log_writer: Writes messages to the log file
    '''

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
        for i in range(1,4):
            path2 = path + str(i)
            # add the account numbers
            for j in range(1,21):
                path3 =  path2 + '/deimos' + str(j)
                # Append the path to the directory list
                dirs.append(path3)
            # Add the engineering folder
            dirs.append(path2 + '/dmoseng')
    if instr == 'ESI':
        for i in range(1,8):
            if i != 5:
                path2 = path + str(i) + '/esi'
                for j in range(1,21):
                    path3 = path2 + str(j)
                    dirs.append(path3)
                dirs.append(path2 + 'eng')  
    elif instr == 'HIRES':
        path += '12'
        for i in range(1,4):
            path2 = path + str(i+4) + '/hires'
            for j in range(1,21):
                path3 = path2 + str(j)
                dirs.append(path3)
            dirs. append(path2 + 'eng')   
    elif instr == 'LRIS':
        path += '24'
        for i in range(1,4):
            path2 = path + str(i) + '/lris'
            for j in range(1,21):
                path3 = path2 + str(j)   
                dirs.append(path3)
            dirs.append(path2 + 'eng')    
    elif instr == 'MOSFIRE':
        path += '1300'    
        for i in range(1,10):
            path2 = path + '/mosfire' + str(i)   
            dirs.append(path2)
        dirs.append(path + '/moseng')    
        dirs.append(path + '/mosfire')
    elif instr == 'NIRC2':
        path += '90'
        for i in range(1,6):
            path2 = path + str(i) + '/nirc'
            for j in range(1,21):
                path3 = path2 + str(j)    
                dirs.append(path3)
        dirs.append(path2 + '2eng')
    elif instr == 'NIRSPEC':
        path += '60'
        for i in range(4):
            path2 = path + str(i) 
            for j in range(1,21):
                path3 = path2 + '/nspec' + str(j) 
                dirs.append(path3)
            dirs.append(path2 + '/nirspec')
            dirs.append(path2 + '/nspeceng')
    elif instr == 'OSIRIS':
        path += '110'    
        for i in range(2):
            path2 = path + str(i)
            for j in range(1,21):
                path3 = path2 + '/osiris'  + str(j)
                dirs.append(path3)
            dirs.append(path2 + '/osiriseng')
            dirs.append(path2 + '/osrseng')
            dirs.append(path2 + '/osiris')
    elif instr == 'KCWI':
        path += '1400/kcwi'
        for i in range(1,10):
            path2 = path + str(i)
            dirs.append(path2)
        dirs.append(path + 'dev')
    elif instr == 'NIRES':
        path += '150'
        for i in range(3):
            path2 = path + str(i) + '/nireseng'
            dirs.append(path2)
    else: # If you get here, you put in a wrong instrument keyword
        log_writer.warn('dep_locate %s: Could not find instrument %s', instr, instr)
        return []

    return dirs
