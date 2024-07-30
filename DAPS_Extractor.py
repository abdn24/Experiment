import re
import csv
import string

DUMP_FILE = "H:\\USD Tether on TRON Experiment\\Tron from Ledger\\Disk AT\\DiskAT.E01"
KEYWORD_FILE = "keywords.txt"
OUTPUT_OFFSETS = "results.csv"

# Read keywords and their corresponding character lengths from the file
keyword_dict = {}
with open(KEYWORD_FILE, 'r') as f:
    for line in f:
        parts = line.strip().split(',')
        if len(parts) == 2:
            keyword, char_length = parts
            keyword_dict[keyword] = int(char_length)

def is_printable(char):
    return char in string.printable and char != '\x7f'

def text_to_pattern(text):
    return [t.encode('utf-8') for t in text.split("?")]

def bytes_to_printable_string(decoded_string):
    result = []
    for char in decoded_string:
        if is_printable(char):
            result.append(char)
        else:
            result.append(''.join(f'\\x{b:02x}' for b in char.encode('utf-8')))
    return ''.join(result)

def _debug_search(pattern, keyword, fh_read, char_length):
    len_pattern = len(b"?".join(pattern))
    read_size = 2**24 - len_pattern
    pattern = [re.escape(p) for p in pattern]
    pattern = b".".join(pattern)
    regex = re.compile(pattern, re.DOTALL+re.MULTILINE+re.IGNORECASE)
    buffer = fh_read(len_pattern + read_size)
    offset = 0
    match = regex.search(buffer)
    all_offsets = []
    while True:
        if not match:
            offset += read_size
            buffer = buffer[read_size:]
            buffer += fh_read(read_size)
            match = regex.search(buffer)
        else:
            print(f"{keyword} - Offset: {offset + match.start():14d} {offset + match.start():12X}")
            context_buffer = buffer[match.start():match.start() + char_length]
            print(context_buffer)
            all_offsets.append((keyword, f"{offset + match.start():12X}", bytes_to_printable_string(context_buffer.decode('utf-8', errors="ignore"))))
            match = regex.search(buffer, match.start() + 1)
        if len(buffer) <= len_pattern:
            return all_offsets

def search(filehandler):
    for keyword, char_length in keyword_dict.items():
        filehandler.seek(0)
        pattern = text_to_pattern(keyword)
        all_offsets = _debug_search(pattern, keyword, filehandler.read, char_length)
        if all_offsets:
            print(f"Matches found for keyword: {keyword}")
            write_to_csv(keyword, all_offsets)
        else:
            print(f"No matches found for keyword: {keyword}")

def write_to_csv(keyword, offsets):
    print(f"Writing to CSV for keyword: {keyword}")
    with open(OUTPUT_OFFSETS, 'a', encoding='utf-8', newline='') as ofp:
        csv_writer = csv.writer(ofp, escapechar='\\')
        for offset in offsets:
            csv_writer.writerow(offset)
            print(f"Written row for offset: {offset}")

def main():
    try:
        filehandler = open(DUMP_FILE, "rb")
        search(filehandler)
        filehandler.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
