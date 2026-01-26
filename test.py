from pathlib import Path

file_list = sorted(
    Path(r".\posts").glob("*2023-09-22*.txt"),
    reverse=True
)

file_names = [f.name for f in file_list]

print(file_names)
