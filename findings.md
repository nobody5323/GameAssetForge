# Findings & Decisions

## Requirements
- Implement the approved GameAsset Forge 12-PR plan.
- Use React + Vite frontend and Python FastAPI backend.
- Provide a working mock flow: prompt compilation, mock asset generation, asset library, quality report, manifest, zip export, simulated cloud upload.
- Preserve a clear PR plan and documentation for competition acceptance.

## Research Findings
- Current repository originally only contained the design document.
- Python 3.13.7, Node v20.20.0, and npm 10.8.2 are installed.
- The design document emphasizes three differentiators: Prompt Compiler, Asset Quality Inspector, and Cloud Asset Hub.
- OpenAI official models page is available at `https://platform.openai.com/docs/models` and includes current GPT Image and GPT-5 model families.

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| JSON DB at `storage/db.json` | Simple MVP persistence without database setup. |
| Runtime mock PNG creation | Avoids checked-in binary generation while keeping demo runnable. |
| Pydantic models | Explicit request/response interfaces for FastAPI docs. |
| Frontend hashless local state refresh | Simple enough for MVP and avoids routing dependency. |
| GPT Image as prompt target profile in PR5 | PR5 only compiles prompts; it does not call image generation APIs. |
| `OPENAI_PROMPT_MODEL` config for text LLM | Keeps the text prompt generation model configurable as OpenAI model availability changes. |
| Rule fallback remains mandatory | Keeps tests and demo runnable without real API keys. |
| Runtime LLM config API stores keys only in process memory | Lets users test LLM from the frontend without committing secrets. |
| LLM config includes Base URL | Supports official OpenAI and OpenAI-compatible gateways. |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
| PowerShell background Uvicorn launch did not persist reliably during PR5 | Verified backend through pytest/TestClient and foreground Uvicorn startup; use foreground command for manual API checks. |
| Existing frontend source had corrupted Chinese text before PR5 | Rewrote visible labels and default copy while preserving the pixel UI style. |

## Resources
- Local design doc: `GameAssetForge工程设计文档`
- Project root: `C:\Users\970892102\Desktop\GameAssetForge`
- OpenAI official models page: `https://platform.openai.com/docs/models`

## Visual/Browser Findings
- PR5 frontend dev server returned app HTML from `http://127.0.0.1:4173/`.
