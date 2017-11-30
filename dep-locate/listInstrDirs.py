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
    dirs = [] 
    path = '/s/sdata'

    switch(instr):
        case 'DEIMOS':
            path += '100'
            # add the instrument 
            for i in range(3):
                path2 = path + str(i+1)
                # add the account number
                for i in range(20):
                    path3 = '/deimos' + path2 + str(i+1)
                    dirs.append(path3)
                dirs.append(path2 + '/dmoseng')
            break
        case 'ESI':
            path += '70'
            for i in range(7):
                if i != 4:
                    path2 = path + str(i+1) + '/esi'
                    for i in range():
                        path3 = path2 + str(i+1)
                        dirs.append(path3)
                    dirs.append(path2 + 'eng')  
            break
        case 'HIRES':
            path += '12'
            for i in range(3):
                path2 = path + str(i+5) + '/hires'
                for i in range(20):
                    path3 = path2 + str(i+1)
                    dirs.append(path3)
                dirs. append(path2 + 'eng')   
            break
        case 'LRIS':
            path += '24'
            for i in range(3):
                path2 = path + str(i+1) + '/lris'
                for i in range(20) 
                    path3 = path2 + str(i+1)   
                    dirs.append(path3)
                dirs.append(path2 + 'eng')    
            break
        case 'MOSFIRE':
            path += '1300'    
            for i in range(9):
                path2 = path + '/mosfire' + str(i+1)   
                dirs.append(path2)
            dirs.append(path + '/moseng')    
            dirs.append(path + '/mosfire')
            break
        case 'NIRC2':
            path += '90'
            for i in range(5):
                path2 = path + str(i) + '/nirc'
                for i in range(20):
                    path3 = path2 + str(i+1)    
                    dirs.append(path3)
            dirs.append(path2 + '2eng')
            break
        case 'NIRSPEC':
            path += '60'
            for i in range(4):
                path2 = path + str(i) 
                for i in range(20):
                    path3 = '/nspec'_+  path2 + str(i+1) 
                    dirs.append(path3)
                dirs.append(path2 + '/nirspec')
                dirs.append(path2 + '/nspeceng')
            break
        case 'OSIRIS':
            path += '110'    
            for i in range(2):
                path2 = path + str(i)
                for i in range(20):
                    path3 = path2 + '/osiris'  + str(i+1)
                    dirs.append(path3)
                dirs.append(path2 + '/osiriseng')
                dirs.append(path2 + 'osrseng')
                dirs.append(path2)
            break    
        case 'KCWI':
            path += '1400/kcwi'
            for i in range(9):
                path2 = path + str(i+1)
                dirs.append(path2)
            dirs.append(path + 'dev')
        default:
            logging.basicConfig(filename='debug.log', level=logging.DEBUG)
            logging.warning('dep_locate %s: Could not find instrument %s', instr, instr)
            print('dep_locate %s: Could not find instrument %s', instr, instr)
            break

    return dirs
