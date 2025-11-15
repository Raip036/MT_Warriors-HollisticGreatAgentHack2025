const BACKEND_URL = "http://localhost:8000";

export async function askBackend(question: string) {
  try {
    const res = await fetch(`${BACKEND_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: question }),
    });

    if (!res.ok) throw new Error("Backend error " + res.status);
    return await res.json();
  } catch (err) {
    console.error(err);
    return { error: "Failed to connect to backend" };
  }
}
