---
name: feedback-mcp-supabase
description: Não usar MCP do Supabase neste projeto — o MCP conectado pertence ao projeto de trabalho, não ao TCC
metadata:
  type: feedback
---

Não usar as ferramentas MCP do Supabase (`mcp__claude_ai_Supabase__*`) neste projeto.

**Why:** O MCP conectado aponta para o projeto Supabase do trabalho do usuário. O TCC usa uma conta Supabase pessoal separada, acessada apenas via supabase-py com as credenciais do `.env`.

**How to apply:** Para qualquer operação no Supabase deste projeto, usar o cliente Python (`supabase-py`) com `SUPABASE_URL` e `SUPABASE_KEY` do `.env`, nunca as ferramentas MCP.
