import logging
import os


def get_logger(name, filename=None, foldername="Logs"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # if not os.path.exists(foldername):
    #     os.makedirs(foldername)
    
    # fh = logging.FileHandler(f"{foldername}/{filename if filename else name}.log")
    # fh.setLevel(logging.DEBUG)
    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    # add the handlers to the logger
    # logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger