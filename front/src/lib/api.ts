const API_BASE = "http://localhost:8000";
export async function executeSimple(message: string): Promise<string> {
  const res = await fetch(`${API_BASE}/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function executeWithPdf(
  message: string,
  pdf: File
): Promise<{ message: string; pdf_path: string; result: unknown }> {
  const formData = new FormData();
  formData.append("user_input", message);
  formData.append("pdf", pdf);

  const res = await fetch(`${API_BASE}/execute-with-pdf`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
