import os
import json
import uuid
import argparse

def anonymize_files(loc):
    # Ensure the folder exists
    if not os.path.exists(loc):
        print(f"Folder '{loc}' does not exist.")
        return

    # Create the destination folder
    anon_loc = f"{loc}_anon"
    if not os.path.exists(anon_loc):
        os.makedirs(anon_loc)

    metadata = {}

    # Process each file in the folder
    for filename in os.listdir(loc):
        file_path = os.path.join(loc, filename)

        # Check if it's a file and not a directory
        if os.path.isfile(file_path):
            # Generate a new UUID and keep the file extension
            extension = os.path.splitext(filename)[1]
            new_filename = f"{uuid.uuid4()}{extension}"
            new_file_path = os.path.join(anon_loc, new_filename)

            # Create a symlink to the file
            os.symlink(os.path.abspath(file_path), new_file_path)

            # Add entry to metadata
            metadata[new_filename] = filename

    # Write the metadata to a JSON file
    with open(os.path.join(anon_loc, 'metadata.json'), 'w') as meta_file:
        json.dump(metadata, meta_file, indent=4)

    print(f"Anonymization complete. Symlinks are stored in '{anon_loc}'")

def main():
    parser = argparse.ArgumentParser(description="Anonymize files in a folder using symlinks")
    parser.add_argument("location", help="The location of the folder to anonymize")

    args = parser.parse_args()
    anonymize_files(args.location)

if __name__ == "__main__":
    main()
