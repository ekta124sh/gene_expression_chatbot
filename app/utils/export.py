"""Export helpers — CSV and Excel with formatted headers."""

import io
import pandas as pd


def export_to_excel(df: pd.DataFrame) -> bytes:
    """Return Excel bytes with auto-fitted column widths."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="GeneXA Results")
        ws = writer.sheets["GeneXA Results"]
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)
    return buf.getvalue()


def export_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")
