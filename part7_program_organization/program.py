# import math as m
# import sys
# from math import ceil

# import foo

# if __name__ == "__main__":
#     foo.grok(...)
#     foo.spam(...)
#     m.acos(...)
#     ceil(...)

#     sys.modules.keys()

# foo.__file__


# Provide a filename
def read_data(filename: str) -> list[str]:
    records = []
    with open(filename) as f:
        for line in f:
            ...
            records.append(r)
    return records




# Provide lines
def read_data(lines):
    records = []
    for line in lines:
        ...
        records.append(r)
    return records

# if __name__ == "__main__":
d = read_data("file.csv")

with open("file.csv") as f:
    d = read_data(f)
