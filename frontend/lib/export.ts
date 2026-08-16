/**
 * Downloads an array of records as a formatted CSV file in the browser.
 */
export function exportToCSV<T extends Record<string, unknown>>(
  filename: string,
  data: T[],
  columns?: Array<{ key: keyof T | string; label: string }>,
) {
  if (!data || data.length === 0) {
    alert("No data available to export.");
    return;
  }

  // Derive column headers
  const headers = columns
    ? columns
    : Object.keys(data[0]).map((k) => ({ key: k, label: k }));

  const csvRows: string[] = [];

  // Header row
  csvRows.push(headers.map((h) => `"${h.label.replace(/"/g, '""')}"`).join(","));

  // Data rows
  for (const row of data) {
    const values = headers.map((h) => {
      const val = row[h.key as keyof T];
      if (val === null || val === undefined) return '""';
      if (typeof val === "object") {
        return `"${JSON.stringify(val).replace(/"/g, '""')}"`;
      }
      return `"${String(val).replace(/"/g, '""')}"`;
    });
    csvRows.push(values.join(","));
  }

  const csvString = csvRows.join("\r\n");
  const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  const dateStr = new Date().toISOString().split("T")[0];
  link.setAttribute("href", url);
  link.setAttribute("download", `${filename}_${dateStr}.csv`);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
