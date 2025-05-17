from langchain.tools import tool

@tool
def extract_table_summary(sample: dict) -> dict:
    """Extracts a summary of numeric rows from the table."""
    table = sample.get("table", [])
    summaries = []
    for row in table[1:]:
        try:
            values = [float(cell.replace("$", "").replace(",", "")) for cell in row[1:] if "$" in cell or cell.replace(".", "").isdigit()]
            if values:
                summaries.append({"label": row[0], "min": min(values), "max": max(values), "mean": round(sum(values)/len(values), 2)})
        except:
            continue
    return {"summary": summaries, "row_count": len(summaries)}
