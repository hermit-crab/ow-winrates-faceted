#!/usr/bin/env python3
import sys

from utils import combine_sources

if __name__ == '__main__':
    if not sys.argv[3:]:
        print('command target_file target_file... output_file')
        sys.exit(1)
    combine_sources(sys.argv[1:-1], sys.argv[-1])
