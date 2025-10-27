import argparse
from .harvest import Runner

def main():
    ap = argparse.ArgumentParser(description="Job harvester CLI")
    ap.add_argument("--once", action="store_true", help="Run a single cycle and exit")
    args = ap.parse_args()
    r = Runner()
    if args.once:
        print(r.run_once())
    else:
        print("Use --once or run the FastAPI app.")

if __name__ == "__main__":
    main()
