import logging as lg
import subprocess as sp
from os import getlogin


def logInfo(message):
    user = getlogin()
    user = __name__ + ' - ' + user
    logger = lg.getLogger(user)
    logger.setLevel(lg.INFO)
    
    handler = lg.FileHandler('info.log')
    handler.setLevel(lg.INFO)
    
    fmat = lg.Formatter('%(name)s - %(asctime)s: %(message)s')
    handler.setFormatter(fmat)
    
    logger.addHandler(handler)

    logger.info(message)

#--------------End logInfo-------------------

def logDebug(message):
    user = getlogin()
    user = __name__ + ' - ' + user
    logger = lg.getLogger(user)
    logger.setLevel(lg.DEBUG)

    handler = lg.FileHandler('debug.log')
    handler.setLevel(lg.DEBUG)

    fmat = lg.Formatter('%(name)s - %(asctime)s: %(message)s')
    handler.setFormatter(fmat)

    logger.addHandler(handler)

    logger.debug(message)

#-----------End logDebug---------------------------

def logWarning(message):
    user = getlogin()
    user = __name__ + ' - ' + user
    logger = lg.getLogger(user)
    logger.setLevel(lg.WARNING)

    handler = lg.FileHandler('warning.log')
    handler.setLevel(lg.WARNING)

    fmat = lg.Formatter('%(name)s - %(asctime)s: %(message)s')
    handler.setFormatter(fmat)

    logger.addHandler(handler)

    logger.debug(message)

#-----------End logWarning-------------------------

def logError(message):
    user = getlogin()
    user = __name__ + ' - ' + user
    logger = lg.getLogger(user)
    logger.setLevel(lg.ERROR)

    handler = lg.FileHandler('error.log')
    handler.setLevel(lg.ERROR)

    fmat = lg.Formatter('%(name)s - %(asctime)s: %(message)s')
    handler.setFormatter(fmat)

    logger.addHandler(handler)

    logger.debug(message)

#------------End logError--------------------------

def logCritical(message):
    user = getlogin()
    user = __name__ + ' - ' + user
    logger = lg.getLogger(user)
    logger.setLevel(lg.CRITICAL)

    handler = lg.FileHandler('critical.log')
    handler.setLevel(lg.CRITICAL)

    fmat = lg.Formatter('%(name)s - %(asctime)s: %(message)s')
    handler.setFormatter(fmat)

    logger.addHandler(handler)

    logger.debug(message)

#-------------End logCritical-----------------------
