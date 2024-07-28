import re
import sys
import os
import getopt
from mmap import ACCESS_READ, mmap
from hashlib import sha256
import base58


# Global Variables
version_number = "1.3"
author = "Created by NDCRTC (ndcrtc@svpnpa.gov.in)"

file_to_examine = ""
shortest_length = 33
address_passed_found = 0
files_examined = 0
total_file_size = 0
quick_mode = False

byte_length_group = [20, 21]

# Tron address: 34 Base58Check encoded characters
patterns_group = [b'T[a-km-zA-HJ-NP-Z1-9]{33}']
names_group = ['Tron address']

def validate_tron_address(address):
    # Check if the address is a base58 encoded string of the correct length
    if not re.match(r"^[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{34}$", address):
        # print("Not Matching\n")
        return False

    # Decode the base58 address
    try:
        decoded_address = base58.b58decode(address).hex()
    except Exception as e:
        return False

    # Check if the address has a valid prefix (41)
    if not decoded_address.startswith("41"):
        # print("Address not starting with 41\n")
        return False

    # Perform a basic checksum validation
    # print("Decoded Address is : ",decoded_address)
    address_bytes = bytes.fromhex(decoded_address)
    # print('Address Bytes are', address_bytes)
    checksum1 = address_bytes[-4:]
    # print ("Checksum1 is", checksum1)
    address_data = address_bytes[:-4]
    checksum2 = sha256(sha256(address_data).digest()).digest()[:4]
    # print("Checksum2 is", checksum2)

    if checksum1 != checksum2:
        return False

    else:
        return True

def examine_file(file_2_examine):
    global files_examined, address_passed_found, total_file_size

    if not os.path.exists(file_2_examine):
        sys.stdout.write(file_2_examine + " : Not found.")
        return

    file_size = os.path.getsize(file_2_examine)
    sys.stdout.write("\n" + "===========================================================" + "\n")
    sys.stdout.write(author + "\n")
    sys.stdout.write("===========================================================" + "\n" + "\n")
    sys.stdout.write("\rScanning: " + file_2_examine + " (" + str(file_size) + " bytes)" + "\n")

    if file_size < shortest_length:
        sys.stdout.write("File too short")
        return

    files_examined += 1
    total_file_size += file_size

    try:
        with open(file_2_examine, 'rb') as f, mmap(f.fileno(), 0, access=ACCESS_READ) as mm:
            for x in range(len(patterns_group)):
                sys.stdout.write("\r                                                                         ")
                sys.stdout.write("\rSearching for: " + names_group[x])
                sys.stdout.flush()

                for match in re.finditer(patterns_group[x], mm):
                    s = match.start()
                    e = match.end()
                    address_match_found = mm[s:e].decode("utf-8")

                   
                    # Validate the Tron address using the function
                    if x == 0 and validate_tron_address(address_match_found):
                        address_passed_found += 1
                        output_file.write('"' + str(address_match_found) + '","' + file_2_examine + '","' + str(s) + '","' + names_group[x] + '"\n')
                    

    except PermissionError as e:
        sys.stdout.write("PermissionError: %s" % str(e))

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:q", ["file=", "quick"])
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-h':
            print("Help message")
            sys.exit()
        elif opt in ("-f", "--file"):
            file_to_examine = arg
        
    if not file_to_examine:
        print("Please specify a file with the -f or --file option.")
        sys.exit(2)

    output_file = open("found_addresses.csv", "w")
    output_file.write('"Address","File","Offset","Type"\n')

    examine_file(file_to_examine)
    
    output_file.close()
    print(f"\nFinished! Examined {files_examined} files, {total_file_size} bytes. Found {address_passed_found} addresses. Results saved to found_addresses.csv.")
