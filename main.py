import os

from dxf_to_shp import DXFtoSHP


def main():
    # check if folders IN and OUT exist, if no: create them
    input_folder_path = 'IN'
    output_folder_path = 'OUT'
    if not os.path.isdir(input_folder_path):
        os.mkdir(input_folder_path)
    if not os.path.isdir(output_folder_path):
        os.mkdir(output_folder_path)

    all_input_files = os.listdir(input_folder_path)
    for input_file in all_input_files:
        if input_file[-4:] == '.dxf':
            print(input_file)
            exporter = DXFtoSHP(
                input_folder_path=input_folder_path,
                output_folder_path=output_folder_path,
                dxf_file_name=input_file
            )
            exporter.run()

if __name__ == "__main__":
    main()