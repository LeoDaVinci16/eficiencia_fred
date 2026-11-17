from pathlib import Path
import re

import pandas as pd


def main():
	project_dir = Path(__file__).resolve().parent.parent
	input_dir = project_dir / "raw" / "dataExport"
	output_dir = project_dir / "raw" / "csv"
	output_dir.mkdir(parents=True, exist_ok=True)

	for excel_path in input_dir.glob("*.xlsx"):
		with pd.ExcelFile(excel_path) as workbook:
			multiple_sheets = len(workbook.sheet_names) > 1
			for sheet_name in workbook.sheet_names:
				safe_name = re.sub(r'[<>:"/\\|?*]', "_", sheet_name).strip(" .")
				suffix = f"_{safe_name}" if multiple_sheets else ""
				output_path = output_dir / f"{excel_path.stem}{suffix}.csv"
				pd.read_excel(workbook, sheet_name=sheet_name).to_csv(
					output_path, index=False, encoding="utf-8-sig"
				)


if __name__ == "__main__":
	main()
