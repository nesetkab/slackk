from database_helpers import enter_data


def main(client=None, submitting_user="Unknown User"):
    """
    Main function to trigger the data entry process into the database.
    Accepts a Slack client and user for error reporting.
    """
    print("Starting data upload process...")
    enter_data("submission_data.json", client, submitting_user)
    print("Data upload process finished.")


if __name__ == "__main__":
    # This allows running the script directly without a Slack context, for testing.
    main()
