import argparse
import os

def read_file(filename):
    if not os.path.exists(filename):
        return []
    
    with open(filename, 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file.readlines()]
    return lines

def write_file(filename, lines):
    with open(filename, 'w', encoding='utf-8') as file:
        file.writelines(f"{line}\n" for line in lines)

def add_entry(filename, name, voice):
    lines = read_file(filename)
    entry = f"{name}={voice}"
    
    if entry not in lines:
        lines.append(entry)
        write_file(filename, lines)
        print(f"Added entry: {entry}")
    else:
        print(f"Entry for {name} already exists with voice {voice}")

def change_entry(filename, name, voice):
    lines = read_file(filename)
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{name}="):
            lines[i] = f"{name}={voice}"
            found = True
            break

    if found:
        write_file(filename, lines)
        print(f"Changed entry for {name} to {voice}")
    else:
        print(f"Name {name} not found in the file.")

def remove_entry(filename, name):
    lines = read_file(filename)
    new_lines = [line for line in lines if not line.startswith(f"{name}=")]
    
    if len(new_lines) != len(lines):
        write_file(filename, new_lines)
        print(f"Removed entry for {name}")
    else:
        print(f"Name {name} not found in the file.")

def main():
    parser = argparse.ArgumentParser(description="Modify C_priority_voice.txt based on given parameters.")
    parser.add_argument("-a", action="store_true", help="Add a new entry to the file.")
    parser.add_argument("-c", action="store_true", help="Change an existing entry in the file.")
    parser.add_argument("-r", action="store_true", help="Remove an entry from the file.")
    parser.add_argument("-n", type=str, required=True, help="Name to be added/changed/removed.")
    parser.add_argument("-v", type=str, help="Voice associated with the name (required for -a and -c).")
    
    args = parser.parse_args()
    
    filename = "C_priority_voice.txt"
    
    if args.a:
        if args.v:
            add_entry(filename, args.n, args.v)
        else:
            print("Error: -v is required for adding an entry (-a).")
    elif args.c:
        if args.v:
            change_entry(filename, args.n, args.v)
        else:
            print("Error: -v is required for changing an entry (-c).")
    elif args.r:
        remove_entry(filename, args.n)
    else:
        print("Error: You must specify one of -a, -c, or -r.")

if __name__ == "__main__":
    main()
