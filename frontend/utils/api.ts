const BACKEND_URL = "http://localhost:8000";

export async function askBackend(
  question: string,
  onProgress?: (message: string) => void
): Promise<{ response: string; citations: string[]; trace?: any; error?: string }> {
  return new Promise((resolve, reject) => {
    try {
      // Use fetch with streaming for Server-Sent Events
      fetch(`${BACKEND_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question }),
      })
        .then(async (res) => {
          if (!res.ok) throw new Error("Backend error " + res.status);

          const reader = res.body?.getReader();
          const decoder = new TextDecoder();

          if (!reader) {
            throw new Error("No response body");
          }

          let buffer = "";

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
              if (line.startsWith("data: ")) {
                try {
                  const data = JSON.parse(line.slice(6));
                  
                  if (data.type === "progress") {
                    if (onProgress) {
                      onProgress(data.message);
                    }
                  } else if (data.type === "complete") {
                    resolve({
                      response: data.response,
                      citations: data.citations || [],
                      trace: data.trace || null,
                    });
                    return;
                  } else if (data.type === "error") {
                    reject(new Error(data.error));
                    return;
                  }
                } catch (e) {
                  console.error("Error parsing SSE data:", e);
                }
              }
            }
          }
        })
        .catch((err) => {
          console.error(err);
          reject(err);
        });
    } catch (err) {
      console.error(err);
      reject(err);
    }
  });
}

