import logging

def getLogger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
