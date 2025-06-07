from database_helpers import enter_data


def main():
    """
    Main function to trigger the data entry process into the database.
    """
    print("Starting data upload process...")
    enter_data("submission_data.json")
    print("Data upload process finished.")


if __name__ == "__main__":
    main()
