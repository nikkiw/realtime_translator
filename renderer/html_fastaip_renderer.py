from .base import BaseRenderer
from typing import List, Tuple
from threading import Thread
import time
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
import uvicorn
import asyncio
from openai import AsyncOpenAI




class BrowserModalRenderer(BaseRenderer):
    def __init__(self, target: str,  api_key: str | None = None, host: str = "0.0.0.0", port: int = 8090):#"127.0.0.1"
        super().__init__() 
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OpenAI API key must be provided")     
        self.host = host
        self.port = port
        self.target = target
        self.app = FastAPI()
        self._translations: List[Tuple[str, str]] = []
        self._server_thread: Thread | None = None
        self._uvicorn_server = None
        self._sse_clients = []
        self.client = AsyncOpenAI(api_key=api_key)
        self._context_text = ""
        self._llm_response = ""


        @self.app.get("/", response_class=HTMLResponse)
        async def index():
            html = f"""
            <!doctype html>
            <html lang="ru">
              <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <title>Таблица переводов</title>
                <style>
                  #translationsTable {{
                    width: 100%;
                    height: 60vh;
                    overflow-y: auto;
                    display: block;
                    font-size: 0.65rem;
                  }}
                  #translationsTable th, #translationsTable td {{
                    word-break: break-word;
                    font-size: 0.65rem;
                  }}
                  #contextArea {{
                    min-height: 60px;
                    border: 1px solid #ccc;
                    padding: 8px;
                    margin-bottom: 8px;
                    border-radius: 4px;
                    background: #f8f9fa;
                  }}
                  #llmResponse {{
                    min-height: 40px;
                    border: 1px solid #eee;
                    padding: 8px;
                    border-radius: 4px;
                    background: #f6f6f6;
                    margin-top: 8px;
                    font-size: 0.9rem;
                  }}
                </style>
              </head>
              <body>
                <div class="container mt-4">
                  <h5>Таблица переводов</h5>
                  <table class="table table-bordered" id="translationsTable">
                    <thead>
                      <tr>
                        <th style="width:40%;">Source</th>
                        <th style="width:40%;">Translation</th>
                        <th style="width:20%;">Action</th>
                      </tr>
                    </thead>
                    <tbody id="tableBody">
                      <!-- Data will be loaded dynamically -->
                    </tbody>
                  </table>
                  <div class="mt-3">
                    <label class="form-label"><b>Context (editable):</b></label>
                    <div id="contextArea" contenteditable="true"></div>
                    <button class="btn btn-primary btn-sm mt-2" onclick="sendContextToLLM()">Send context to LLM</button>
                    <div id="llmResponse" class="mt-2"></div>
                  </div>
                </div>
                <script>
                  let context = [];
                  let suppressContextUpdate = false;

                  async function fetchTranslations() {{
                    const resp = await fetch('/translations');
                    const data = await resp.json();
                    updateTable(data);
                  }}

                  async function fetchContextAndLLM() {{
                    const resp = await fetch('/context_llm');
                    const data = await resp.json();
                    suppressContextUpdate = true;
                    document.getElementById('contextArea').innerText = data.context || "";
                    context = (data.context || "").split('\\n');
                    document.getElementById('llmResponse').innerText = data.llm_response || "";
                    suppressContextUpdate = false;
                  }}

                  function updateTable(data) {{
                    const tbody = document.getElementById('tableBody');
                    tbody.innerHTML = '';
                    data.forEach(([src, dst], idx) => {{
                      const tr = document.createElement('tr');
                      tr.innerHTML = `
                        <td style="font-size:0.85rem;">${{src}}</td>
                        <td style="font-size:0.85rem;">${{dst}}</td>
                        <td>
                          <button class="btn btn-sm btn-success" onclick="addToContext(${{idx}})">+</button>
                        </td>
                      `;
                      tbody.appendChild(tr);
                    }});
                    window._lastTranslations = data;
                  }}

                  function addToContext(idx) {{
                    const data = window._lastTranslations || [];
                    if (data[idx]) {{
                      const text = data[idx][0];
                      context.push(text);
                      updateContextArea();
                      sendContextUpdate();
                    }}
                  }}

                  function updateContextArea() {{
                    const area = document.getElementById('contextArea');
                    area.innerText = context.join('\\n');
                  }}

                  async function sendContextUpdate() {{
                    // Send updated context to server (without LLM request)
                    const area = document.getElementById('contextArea');
                    const ctx = area.innerText;
                    await fetch('/update_context', {{
                      method: 'POST',
                      headers: {{'Content-Type': 'application/json'}},
                      body: JSON.stringify({{context: ctx}})
                    }});
                  }}

                  document.addEventListener('DOMContentLoaded', function() {{
                    const area = document.getElementById('contextArea');
                    area.addEventListener('input', function() {{
                      if (!suppressContextUpdate) {{
                        context = area.innerText.split('\\n');
                        sendContextUpdate();
                      }}
                    }});
                  }});

                  async function sendContextToLLM() {{
                    const area = document.getElementById('contextArea');
                    const ctx = area.innerText;
                    const resp = await fetch('/llm_context', {{
                      method: 'POST',
                      headers: {{'Content-Type': 'application/json'}},
                      body: JSON.stringify({{context: ctx}})
                    }});
                    // Response and context will be updated via SSE
                  }}

                  // SSE for updating translations and context/LLM
                  const evtSource = new EventSource('/events');
                  evtSource.onmessage = function(event) {{
                    fetchTranslations();
                    fetchContextAndLLM();
                  }};

                  // Initial load
                  fetchTranslations();
                  fetchContextAndLLM();
                </script>
              </body>
            </html>
            """
            return HTMLResponse(content=html)

        @self.app.get("/translations")
        async def get_translations():
            return JSONResponse(self._translations)

        @self.app.get("/context_llm")
        async def get_context_llm():
            return JSONResponse({
                "context": self._context_text,
                "llm_response": self._llm_response
            })

        @self.app.post("/update_context")
        async def update_context(request: Request):
            data = await request.json()
            self._context_text = data.get("context", "")
            # Clear LLM response when context changes
            self._llm_response = ""
            # Notify all clients
            for queue in list(self._sse_clients):
                try:
                    queue.put_nowait(True)
                except Exception:
                    pass
            return JSONResponse({"ok": True})

        @self.app.get("/events")
        async def sse(request: Request):
            async def event_generator():
                queue = asyncio.Queue()
                self._sse_clients.append(queue)
                try:
                    while True:
                        # Exit if client disconnects
                        if await request.is_disconnected():
                            break
                        try:
                            await asyncio.wait_for(queue.get(), timeout=15)
                            yield "data: update\n\n"
                        except asyncio.TimeoutError:
                            # Keep-alive ping
                            yield ": keep-alive\n\n"
                finally:
                    self._sse_clients.remove(queue)
            return StreamingResponse(event_generator(), media_type="text/event-stream")

        @self.app.post("/llm_context")
        async def llm_context(request: Request):
            data = await request.json()
            context_text = data.get("context", "")
            self._context_text = context_text

            async def my_llm_ask(context_text: str) -> str:
                api_key = os.environ.get("OPENAI_API_KEY", "")
                if not api_key:
                    return "OPENAI_API_KEY not set"
                prompt = (
                    "You are an assistant for software engineering interviews. "
                    f"Answer the question and add translate in {self.target} after ===================\n\n"
                    f"Context:\n{context_text}"
                )
                try:
                    response = await self.client.chat.completions.create(
                        model="gpt-4.1-mini",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=3000,
                    )
                    if response.choices and response.choices[0].message:
                        return response.choices[0].message.content or ""
                    return ""
                except Exception as e:
                    return f"Error: {str(e)}"

            self._llm_response = await my_llm_ask(context_text)
            # Notify all clients
            for queue in list(self._sse_clients):
                try:
                    queue.put_nowait(True)
                except Exception:
                    pass
            return JSONResponse({"response": self._llm_response})

    def run(self):
        """Run Uvicorn in a background thread."""
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="warning")
        self._uvicorn_server = uvicorn.Server(config)

        def _serve():
            # This method blocks until the server is stopped
            self._uvicorn_server.run()

        self._server_thread = Thread(target=_serve, daemon=True)
        self._server_thread.start()
        # Give the server time to start
        time.sleep(0.5)

    def render(self, translations: List[Tuple[str, str]]):
        """Update data and send event to clients."""
        self._translations = translations[::-1]
        # Notify all subscribed clients
        for queue in list(self._sse_clients):
            try:
                queue.put_nowait(True)
            except Exception:
                pass
        # Open browser only on first run
        # if not hasattr(self, "_browser_opened"):
            # url = f"http://{self.host}:{self.port}/"
            # webbrowser.open(url)
            # self._browser_opened = True

    def stop(self):
        """Stop the server."""
        if self._uvicorn_server and self._uvicorn_server.should_exit is False:
            self._uvicorn_server.should_exit = True
        if self._server_thread:
            self._server_thread.join(timeout=1)