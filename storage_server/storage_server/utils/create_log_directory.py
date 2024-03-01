import os


def create_log_directory():
    log_dir = 'logs/'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = 'logfile' + '.log'
    log_path = os.path.join(log_dir, log_file)

    return log_path
