"""Helper to document where CICIDS2017 comes from.

The dataset itself is NOT committed to git (see .gitignore).
This script exists to document the source and expected layout
for anyone cloning the repo.

Download manually from:
    https://www.kaggle.com/datasets/shadman1028/cicids2017-official-flow-feature-csv-files

Expected files inside ml/datasets/cicids2017/:
    Monday-WorkingHours.pcap_ISCX.csv
    Tuesday-WorkingHours.pcap_ISCX.csv
    Wednesday-workingHours.pcap_ISCX.csv
    Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv
    Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv
    Friday-WorkingHours-Morning.pcap_ISCX.csv
    Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
    Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv

Usage:
    Place the 8 CSVs inside ml/datasets/cicids2017/ and run any
    script under ml/training/.
"""

from pathlib import Path

DATA_DIR = Path(__file__).parent / "cicids2017"

EXPECTED_FILES = [
    "Monday-WorkingHours.pcap_ISCX.csv",
    "Tuesday-WorkingHours.pcap_ISCX.csv",
    "Wednesday-workingHours.pcap_ISCX.csv",
    "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv",
    "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv",
    "Friday-WorkingHours-Morning.pcap_ISCX.csv",
    "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
    "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
]


def main() -> None:
    missing = [name for name in EXPECTED_FILES if not (DATA_DIR / name).exists()]
    if missing:
        print(f"Missing {len(missing)} file(s) in {DATA_DIR}:")
        for name in missing:
            print(f"  - {name}")
    else:
        print(f"All {len(EXPECTED_FILES)} CICIDS2017 files present in {DATA_DIR}")


if __name__ == "__main__":
    main()
