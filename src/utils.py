def _read_file_lines(file_path):
    try:
        with open(file_path, 'r', encoding='utf8') as f:
            return [line.split('-*', 1)[0].strip().lower() for line in f]
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return [] 
