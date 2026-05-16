
import sys

def count_braces(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    open_braces = 0
    close_braces = 0
    line_num = 0
    for line in content.split('\n'):
        line_num += 1
        for char in line:
            if char == '{':
                open_braces += 1
            elif char == '}':
                close_braces += 1
        
        if close_braces > open_braces:
            print(f"Excess closing brace at line {line_num}")
            # Reset to continue finding others
            open_braces = close_braces 

    print(f"Total Open: {open_braces}")
    print(f"Total Close: {close_braces}")

if __name__ == "__main__":
    count_braces(sys.argv[1])
