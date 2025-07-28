#!/usr/bin/env python3
"""Quick CLI to test the signup-list regex logic.

Usage:
  python signup_parse_test.py -f message.txt
  cat message.txt | python signup_parse_test.py
  python signup_parse_test.py "1) Bob\n2) Alice\n3)" 
"""
import sys, argparse, textwrap
from whatsapp_automation import _parse_signup_list

parser = argparse.ArgumentParser(description="Test the numbered-list parser")
parser.add_argument("text", nargs="?", help="Message text (if omitted, read stdin)")
parser.add_argument("-f", "--file", help="Path to file containing message text")
args = parser.parse_args()

if args.file:
    with open(args.file, "r", encoding="utf-8") as fh:
        raw = fh.read()
elif args.text:
    raw = args.text
else:
    raw = sys.stdin.read()

result = _parse_signup_list(raw)
print("----- INPUT -----\n" + raw)
print("----- PARSE RESULT -----")
if result:
    total, names = result
    print("Total bullets:", total)
    print("Names          :", names)
    filled = [n for n in names if n]
    print("Filled count   :", len(filled))
else:
    print("Parser returned None (pattern not recognised)") 