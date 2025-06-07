import hickle as hkl
import os

# The file that stores the entry count
COUNTER_FILE = "entrys"


def reset_counter():
    """Resets the entry counter to zero."""
    try:
        print(f"Resetting counter in file '{COUNTER_FILE}' to 0...")
        hkl.dump(0, COUNTER_FILE, mode="w")
        print("Counter has been successfully reset.")
    except Exception as e:
        print(f"An error occurred while resetting the counter: {e}")


if __name__ == "__main__":
    if (
        input(
            f"Are you sure you want to reset the entry counter file '{COUNTER_FILE}' to 0? (yes/no): "
        ).lower()
        == "yes"
    ):
        reset_counter()
    else:
        print("Counter reset cancelled.")
