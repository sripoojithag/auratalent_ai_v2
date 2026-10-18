import express from "express";
import { existsSync } from "fs";
import path from "path";
import { spawn, ChildProcess } from "child_process";
import { createServer as createViteServer, ViteDevServer } from "vite";

const app = express();
const PORT = 3000;
const FASTAPI_PORT = 8081;

let fastApiProcess: ChildProcess | null = null;
let vite: ViteDevServer | null = null;

function startFastAPI() {
  console.log(`[server.ts] Starting FastAPI uvicorn on port ${FASTAPI_PORT}...`);
  try {
    const venvPython = path.join(
      process.cwd(),
      ".venv",
      process.platform === "win32" ? "Scripts" : "bin",
      process.platform === "win32" ? "python.exe" : "python",
    );
    const python = process.env.PYTHON || (existsSync(venvPython)
      ? venvPython
      : process.platform === "win32" ? "python" : "python3");

    fastApiProcess = spawn(
      python,
      ["-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", String(FASTAPI_PORT)],
      {
        env: { ...process.env, PYTHONPATH: "." },
        stdio: "inherit",
      }
    );

    fastApiProcess.on("error", (err) => {
      console.error("[server.ts] FastAPI spawn error:", err);
    });

    fastApiProcess.on("exit", (code, signal) => {
      console.log(`[server.ts] FastAPI exited with code ${code}, signal ${signal}`);
    });
  } catch (err) {
    console.error("[server.ts] Failed to spawn FastAPI:", err);
  }
}

// Robust proxy to FastAPI with retry loop while FastAPI is warming up
app.use("/api", async (req, res) => {
  const targetUrl = `http://127.0.0.1:${FASTAPI_PORT}/api${req.url}`;
  const headers: Record<string, string> = {};
  for (const [key, val] of Object.entries(req.headers)) {
    if (key.toLowerCase() !== "host" && val) {
      headers[key] = Array.isArray(val) ? val.join(", ") : val;
    }
  }

  const fetchOptions: RequestInit = {
    method: req.method,
    headers,
  };

  if (req.method !== "GET" && req.method !== "HEAD") {
    const chunks: Buffer[] = [];
    for await (const chunk of req) {
      chunks.push(typeof chunk === "string" ? Buffer.from(chunk) : chunk);
    }
    fetchOptions.body = Buffer.concat(chunks);
    // @ts-ignore
    fetchOptions.duplex = "half";
  }

  let attempts = 0;
  const maxAttempts = 15;
  while (attempts < maxAttempts) {
    try {
      const apiResponse = await fetch(targetUrl, fetchOptions);

      res.status(apiResponse.status);
      apiResponse.headers.forEach((val, key) => {
        if (!["content-encoding", "transfer-encoding"].includes(key.toLowerCase())) {
          res.setHeader(key, val);
        }
      });

      const bodyBuffer = Buffer.from(await apiResponse.arrayBuffer());
      res.send(bodyBuffer);
      return;
    } catch (err: any) {
      attempts++;
      if (attempts >= maxAttempts) {
        console.error(`[server.ts] Proxy failed after ${maxAttempts} attempts:`, err.message);
        res.status(503).json({
          success: false,
          detail: "FastAPI backend is starting up, please refresh momentarily.",
        });
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, 350));
    }
  }
});

// Root & Static / Vite fallback handler
app.use(async (req, res, next) => {
  if (req.url.startsWith("/api")) {
    return next();
  }

  if (process.env.NODE_ENV !== "production") {
    if (vite) {
      return vite.middlewares(req, res, next);
    }
    res.setHeader("Content-Type", "text/html");
    res.send(`<!DOCTYPE html><html><head><meta http-equiv="refresh" content="1"><title>Loading AuraTalent AI...</title></head><body style="font-family:sans-serif;padding:2rem;text-align:center;"><h2>Starting AuraTalent AI Dev Server...</h2><p>Initializing Vite and FastAPI backend...</p></body></html>`);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    express.static(distPath)(req, res, () => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }
});

// Process cleanup hooks
process.on("exit", () => {
  if (fastApiProcess) fastApiProcess.kill();
});
process.on("SIGINT", () => process.exit());
process.on("SIGTERM", () => process.exit());

// 1. Immediately bind port 3000 so AI Studio health check passes instantly
const server = app.listen(PORT, "0.0.0.0", async () => {
  console.log(`[server.ts] AuraTalent Gateway instantly listening on http://0.0.0.0:${PORT}`);

  // 2. Initialize Vite in the background
  if (process.env.NODE_ENV !== "production") {
    try {
      vite = await createViteServer({
        server: { middlewareMode: true },
        appType: "spa",
      });
      console.log(`[server.ts] Vite middleware loaded successfully.`);
    } catch (err) {
      console.error(`[server.ts] Error creating Vite server:`, err);
    }
  }

  // 3. Defer FastAPI launch slightly so Node has completely bound socket
  setTimeout(() => {
    startFastAPI();
  }, 400);
});
