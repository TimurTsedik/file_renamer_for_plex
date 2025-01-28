import os
import re
import shutil

def recursive_dir_scaner(
        initial_directory: str,
        ignored_names: list[str] = ['TV Shows', '.DS_Store'],
        depth: int = 0
    ) -> list[dict[str, str]]:
    """
    Recursively scans directories and gathers file information with recursion depth.

    :param initial_directory: The base directory to start scanning from.
    :param ignored_names: List of folder or file names to ignore.
    :param depth: Current depth of recursion (starts at 0).
    :return: List of dicts - {'directory': str, 'path': str, 'depth': int}
    """
    directory = os.path.expanduser(initial_directory)
    result = []
    scanned_directories = []
    for sub_directory in os.listdir(directory):
        if sub_directory in ignored_names:
            # dont dive into ignored directories
            continue

        if os.path.isdir(os.path.join(directory, sub_directory)):
            scanned_directories.append(sub_directory)
            result.extend(recursive_dir_scaner(os.path.join(directory, sub_directory), ignored_names, depth + 1))
    for filename in os.listdir(directory):
        if filename in ignored_names:
            # dont dive into ignored directories
            continue
        if os.path.isdir(os.path.join(directory, filename)) and filename not in scanned_directories:
            result.extend(recursive_dir_scaner(os.path.join(directory, filename)), ignored_names, depth + 1)
        else:
            result.append({'directory': directory, 'path': os.path.join(directory, filename), 'depth': depth})
    return result


def file_dir_renamer(initial_directory, leave_originals: bool = True, tv_shows_folder: str = 'TV Shows'):
    """
    Renames and organizes TV show episodes within a specified directory.

    This function scans the given directory recursively for files matching
    certain media extensions and renames them based on a series-season-episode pattern.
    It then organizes these files into a new directory structure under a specified
    "TV Shows" folder, creating folders for each show and season. Optionally,
    it can leave the original files in place or remove them after organizing.

    :param initial_directory: The base directory to start scanning and organizing from.
    :param leave_originals: A flag indicating whether to leave the original files
                            in place (True) or remove them after reorganizing (False).
    :param tv_shows_folder: Name of the folder where TV shows will be organized into.
    """
    directory = os.path.expanduser(initial_directory)
    pattern = r"^(.+?)\.S(\d{2})(?:[.\-]?E(\d{2}))?"
    extensions = ['.mkv', '.mp4', '.avi', '.srt']
    files = recursive_dir_scaner(directory)
    new_dir_structure = []
    # Получили список файлов для переименования эпизодов
    for file in files:
        if file['path'].endswith(tuple(extensions)):
            extension = os.path.splitext(file['path'])[1]
            match = re.search(pattern, file['path'].split('/')[-1], re.IGNORECASE)
            if match:
                series_name = match.group(1).replace('.', ' ')
                season_number = match.group(2)
                episode_number = match.group(3)
                new_filename = f"{series_name} - S{season_number}E{episode_number}{extension}"

                old_file = file['path']
                new_dir_structure.append({
                    'title': series_name,
                    'season': season_number,
                    'new_file_name': new_filename,
                    'old_file_name': old_file,
                    'old_directory': file['directory'],
                    'depth': file['depth']
                })

    # Переносим переименованные файлы в TV Shows / Show_name / Season num / Episode name
    tv_shows = set(new_dir_structure['title'] for new_dir_structure in new_dir_structure)
    for tv_show in tv_shows:
        new_show_dir = os.path.join(directory, tv_shows_folder, tv_show)
        if not os.path.exists(new_show_dir):
            os.mkdir(new_show_dir)
        show_items = [item for item in new_dir_structure if item.get('title') == tv_show]
        seasons = set(shows['season'] for shows in show_items)
        for season in seasons:
            season_dir = os.path.join(directory, tv_shows_folder, tv_show, f'Season {season}')
            if not os.path.exists(season_dir):
                os.mkdir(season_dir)
            episodes = [item for item in show_items if item.get('season') == season]
            for episode in episodes:
                sub_dir_list = episode['old_directory'].split('/')[-(episode['depth'] - 1):] if episode['depth'] > 1 else []
                episode_new_path = os.path.join(directory, tv_shows_folder, tv_show, f'Season {season}', *sub_dir_list, episode['new_file_name'])
                episode_dir = os.path.join(directory, tv_shows_folder, tv_show, f'Season {season}', *sub_dir_list)
                if not os.path.exists(episode_dir):
                    os.mkdir(episode_dir)
                if leave_originals:
                    shutil.copy(episode['old_file_name'], episode_new_path)
                    print(f"Copied {episode['old_file_name']} to {episode_new_path}")
                else:
                    shutil.move(episode['old_file_name'], episode_new_path)
                    print(f"Moved {episode['old_file_name']} to {episode_new_path}")

    old_dirs = set(item['old_directory'] for item in new_dir_structure)
    if not leave_originals:
        for old_dir in old_dirs:
            shutil.rmtree(old_dir)


if __name__ == "__main__":
    file_dir_renamer('~/Movies/Cinema', False, 'TV Shows')
