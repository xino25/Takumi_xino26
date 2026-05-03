from settings import * 

def import_image(*path, format = 'png', alpha = True):
    full_path = join(*path) + f'.{format}'
    return pygame.image.load(full_path).convert_alpha() if alpha else pygame.image.load(full_path).convert()

def import_folder(*path):
    """Load all images in a folder tree.
    - Skips hidden files (like .DS_Store) and non-image files
    - Sorts numerically when filenames start with a number (e.g. 0.png, 10.png)
      otherwise falls back to case-insensitive name sort.
    """
    frames = []
    allowed_exts = {"png", "jpg", "jpeg", "gif"}

    def sort_key(name: str):
        # Split stem and extension
        if "." in name:
            stem, ext = name.rsplit(".", 1)
        else:
            stem, ext = name, ""
        # Try numeric sort first
        if stem.isdigit():
            return (0, int(stem), "")
        # Fallback to alpha sort (case-insensitive)
        return (1, stem.lower(), ext.lower())

    for folder_path, _, file_names in walk(join(*path)):
        # Filter out hidden files and non-image files
        cleaned = []
        for file_name in file_names:
            if not file_name or file_name.startswith('.'):
                continue
            if '.' not in file_name:
                continue
            ext = file_name.rsplit('.', 1)[-1].lower()
            if ext not in allowed_exts:
                continue
            cleaned.append(file_name)

        for file_name in sorted(cleaned, key=sort_key):
            full_path = join(folder_path, file_name)
            frames.append(pygame.image.load(full_path).convert_alpha())
    return frames

def audio_importer(*path):
    audio_dict = {}
    for folder_path, _, file_names in walk(join(*path)):
        for file_name in file_names:
            full_path = join(folder_path, file_name)
            audio_dict[file_name.split('.')[0]] = pygame.mixer.Sound(full_path)
    return audio_dict