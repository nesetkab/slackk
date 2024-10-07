from client_functions import *
import os

def main():
    config = load_config()

    conn = connect(config)

    for file in os.listdir('incoming'):
        enterData("incoming/"+file, conn)

if __name__ == "__main__":
    main()