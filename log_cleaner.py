import argparse
import csv

def build_parser():

    parser = argparse.ArgumentParser(
        description="Cleans up a log file and tallys up the results"
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        default="app.log",
        help="Path to input .log file (default: app.log)"
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on the first invalid entry instead of skipping it."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test mode that disables writing to a csv, but directly prints results to CLI."
    )

    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Path to output CSV file (default: <input>_report.csv)"
    )

    return parser

def output_filename_for(input_file: str) -> str:
    base = input_file.rsplit(".", 1)[0]
    return base + "_report.csv"