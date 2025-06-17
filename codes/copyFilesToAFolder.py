import shutil
import os

source_folder = "/Users/mdrahman/AugustaUniversity/sw/ar/files/allfiles/"
destination_folder = "/Users/mdrahman/AugustaUniversity/idxv2/program/testpdf/"

files_to_copy = ["", ""]


for file_name in files_to_copy:
    src_path = os.path.join(source_folder, file_name)
    dest_path = os.path.join(destination_folder, file_name)

    if os.path.exists(src_path):
        shutil.copy(src_path, dest_path)
        print(f"Copied {file_name} to {destination_folder}")
    else:
        print(f"File {file_name} not found in {source_folder}")