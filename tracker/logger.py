import logging

def setup_logger(name=__name__, log_file="tracker.log"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    """
    Sets up and returns a logger with a given name. Logs both to console and to a file.
    """
    if logger.hasHandlers():
        return logger 

    # Formatter for all  handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Console handler 
    console_handler = logging.StreamHandler() 
    console_handler.setFormatter(formatter)

    # File handler 
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Attach handlers 
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger







