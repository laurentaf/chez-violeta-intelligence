# Chez Violeta — Chatbot de Processos

## 📋 Sobre

Chatbot interativo para funcionários de loja consultarem os processos operacionais da **Chez Violeta** (joias e acessórios).

## 🚀 Como usar

1. **Abra o arquivo** `index.html` em qualquer navegador moderno (Chrome, Firefox, Edge, Safari)
   - Clique duas vezes no arquivo ou arraste para o navegador
   - **Não requer servidor** — o chatbot é totalmente auto-contido (HTML + CSS + JS)

2. **Faça perguntas** sobre os processos operacionais:
   - 📦 *"Chegou mercadoria, o que faço?"*
   - 🏷️ *"Como etiquetar?"*
   - ⚠️ *"A NF não confere com o que chegou"*
   - 📤 *"Preciso devolver mercadoria"*
   - 📱 *"Como bipar?"*
   - 🔄 *"Cliente quer trocar"*
   - 💰 *"Como colocar preço?"*
   - 📋 *"Quem faz o que?"*

3. **Ou clique nos botões de atalho** na tela inicial ou nas sugestões abaixo do input.

## 🎨 Funcionalidades

- 🔍 **Busca por palavra-chave** — digite qualquer termo relacionado ao processo
- 🎯 **Botões de atalho** — perguntas frequentes na tela inicial
- 🌙 **Modo escuro** — clique no ícone de lua no cabeçalho
- 📱 **Responsivo** — funciona em celular e desktop
- 💡 **Respostas completas** — passo a passo detalhado, regras de negócio, SLAs
- 🧹 **Limpar conversa** — botão no cabeçalho para recomeçar

## 📚 Conhecimento embutido

Baseado no documento **Processo de Entrada de Mercadorias** (`artifacts/design/processo-entrada-mercadorias.md`):

| Tópico | O que cobre |
|--------|-------------|
| Recebimento | NF, lançamento no GAVARNIE, envio para conferência |
| Etiquetagem | EAN vs código próprio (CV-XXXXX-NNN) |
| Divergência | Quantidade, item não localizado, excedente |
| Devolução | Fluxo completo ao fornecedor |
| Bipagem | Scan, controles, exceções |
| Troca | Procedimento geral recomendado |
| Precificação | Regras de etiqueta de preço |
| Liberação | Status, dupla assinatura |
| Perda/Extravio | Busca, ocorrência |
| Papéis | Quem faz o que |
| SLAs | Tempos e prazos de cada etapa |
| Glossário | Termos técnicos |
| Regras de Negócio | 10 regras consolidadas |

## 🎨 Design System

- **Paleta:** Vinho `#7B2D4E`, Dourado `#C9A84C`, Off-white `#FAF8F5`
- **Tipografia:** Cormorant Garamond (títulos), Inter/System (corpo)
- **Fonte:** `artifacts/design/design-system.md`

## 🛠️ Recriação

Para regenerar o chatbot a partir da fonte:

```bash
uv run python artifacts/design/chatbot-loja/generate_chatbot.py
```

## 🔗 Referências

- `source.md` — Referência de design
- `processo-entrada-mercadorias.md` — Documento de processo fonte
- `design-system.md` — Design system da Chez Violeta
