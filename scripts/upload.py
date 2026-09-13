#!/usr/bin/env python3
import sys

from utils import upload

if __name__ == '__main__':
    if not sys.argv[2:]:
        print('command target_file destination_file')
        sys.exit(1)
    upload(sys.argv[1], sys.argv[2])
