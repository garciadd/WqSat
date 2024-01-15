
def read_download_file(download):
    # Abre el archivo en modo lectura
    with open(download, 'r') as file:
        # Lee todo el contenido del archivo
        contenido = file.read()

    print(contenido)