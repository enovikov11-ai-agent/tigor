import os

path = "./manuls-dataset"

# Get a list of all files in the folder
files = os.listdir(path)

# Iterate over the files
for i, file in enumerate(files):
    # Skip any non-image files
    if not file.endswith(".jpg"):
        continue

    # Construct the new filename
    new_filename = "dataset-" + str(i).zfill(4) + ".jpg"

    # Rename the file
    os.rename(os.path.join(path, file), os.path.join(path, new_filename))