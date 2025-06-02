from client_functions import *
import os

def main():
    config = load_config()

    conn = connect(config)

    enterData("submission_data.json",conn)
