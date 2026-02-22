import argparse
import csv
import logging

# action and level are necesary

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

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging."
    )

    return parser

def output_filename_for(input_file: str) -> str:
    base = input_file.rsplit(".", 1)[0]
    return base + "_report.csv"

def main():
    

    parser = build_parser()
    args = parser.parse_args()
    
    logging.basicConfig(
        level= logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    input_file = args.input_file
    output_file = args.output if args.output else output_filename_for(input_file)

    valid_lines = 0
    skipped_lines = 0
    blank_lines = 0

    
    levels = {"info": 0, "warn": 0, "error": 0}
    valid_levels = set(levels)
    actions = {}

    try:
        with open(input_file, "r") as file:

            for lineno, line in enumerate(file, start=1):
                if not line.strip():
                    blank_lines += 1
                    continue

                tokens = line.split()

                # Validate that the line is valid
                if len(tokens) < 2:
                    if args.strict:
                        logging.error(
                            "Line %d: invalid format (expected <date> <level> ...). Content=%r",
                            lineno,
                            line
                            )
                        raise SystemExit(1)
                    else:
                        logging.warning(
                            "Line %d: invalid format (expected <date> <level> ...). Content=%r",
                            lineno,
                            line
                            )
                        skipped_lines += 1
                        continue

                date_token = tokens[0].strip()

                # Check that the first token is date + validity
                if len(date_token) != 10 or date_token.count("-") != 2:
                    if args.strict:
                        logging.error("Line %d: invalid date format (expected YYYY-MM-DD). Content=%r",
                                      lineno,
                                      line
                                      )
                        raise SystemExit(1)
                    else:
                        logging.warning("Line %d: invalid date format (expected YYYY-MM-DD). Content=%r",
                                      lineno,
                                      line
                                      )
                        skipped_lines += 1
                        continue

                # Check that second token is valid metric
                level_token = tokens[1].strip().lower()

                if level_token not in valid_levels:
                    if args.strict:
                        logging.error("Line %d: invalid metric (expected info, warn, error). Content=%r",
                                      lineno,
                                      line
                                      )
                        raise SystemExit(1)
                    else:
                        logging.warning("Line %d: invalid metric (expected info, warn, error). Content=%r",
                                      lineno,
                                      line
                                      )
                        skipped_lines += 1
                        continue

                fields = {}
                for token in tokens[2:]:
                    if "=" not in token:
                        continue
                    else:
                        key, value = token.split("=", 1)
                        key = key.strip().lower()
                        value = value.strip()
                        fields[key] = value

                if not fields.get("action"):
                    if args.strict:
                        logging.error("Line %d: invalid metric, action must be included. Content=%r",
                                      lineno,
                                      line)
                        raise SystemExit(1)
                    else:
                        logging.warning("Line %d: invalid metric, action must be included. Content=%r",
                                      lineno,
                                      line)
                        skipped_lines += 1
                        continue

                action = fields.get("action")
                if action not in actions:
                    actions[action] = 0

                actions[action] += 1
                levels[level_token] += 1
                valid_lines += 1
    
    except FileNotFoundError:
        logging.error("File not found: {input_file}")
        raise SystemExit(1)
    
    if not actions:
        logging.error("No valid action data found.")
        raise SystemExit(1)
    
    sorted_actions = sorted(
        actions.items(),
        key=lambda pair: (-pair[1], pair[0])
    )

    top_actions = sorted_actions[:3]
    total_lines = valid_lines + skipped_lines
    
    if args.dry_run:
        logging.info("--- Dry Run ---")
        logging.info("Lines skipped: %d", skipped_lines)
        logging.info("Valid lines: %d", valid_lines)
        logging.info("Total lines: %d", total_lines)

        for level, total in levels.items():
            logging.info("%d: %d", level, total)

        logging.info("--- Top Actions ---")
        for action, count in top_actions:
            logging.info("%s: %d", action, count)
        return
    
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["category", "total"])
        writer.writerow(["skipped_lines", skipped_lines])
        writer.writerow(["valid_lines", valid_lines])
        writer.writerow(["total_lines", total_lines])
        writer.writerow(["--levels--", ""])
        for level, total in levels.items():
            writer.writerow([level, total])

        writer.writerow(["--top_actions--", ""])
        for action, total in top_actions:
            writer.writerow([action, total])

        print(f"Wrote report: {output_file}")
            

if __name__ == "__main__":
    main()