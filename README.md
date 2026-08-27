# STLFLIX · Dashboard de Engajamento Mensal

Painel comparativo mês a mês da métrica de engajamento (usuários logados
que dispararam 2+ ações dentro do evento `engagement_action_stlflix_v2`).

## Como funciona

1. Todo dia 2 do mês, um robô (GitHub Actions) acorda sozinho e busca no
   Amplitude o snapshot do mês anterior fechado — usando a mesma consulta
   já configurada no gráfico `STLFLIX Engaj - Snapshot`.
2. O número é salvo em `data/history.json` (nunca é recalculado depois).
3. O arquivo `index.html` lê esse histórico e monta o dashboard comparativo.

## Configuração (uma vez só)

### 1. Adicionar as chaves do Amplitude

No repositório, vá em **Settings → Secrets and variables → Actions → New repository secret**
e adicione três segredos:

| Nome | Onde encontrar |
|---|---|
| `AMPLITUDE_API_KEY` | Amplitude → ⚙️ Configurações do projeto → General |
| `AMPLITUDE_SECRET_KEY` | Mesmo lugar, logo abaixo da API Key |
| `AMPLITUDE_CHART_ID` | Abra o gráfico "STLFLIX Engaj" no Amplitude e copie o código que aparece na URL do navegador, algo como `amplitude.com/analytics/.../chart/abc123xyz` → o `abc123xyz` é o Chart ID |

### 2. Ativar o GitHub Pages

Em **Settings → Pages → Source**, selecione **Deploy from a branch**,
branch `main`, pasta `/ (root)`. Depois de salvar, o link do dashboard
aparece ali mesmo (algo como `https://seu-usuario.github.io/nome-do-repo/`).

### 3. Testar

Vá na aba **Actions → Snapshot mensal de engajamento STLFLIX → Run workflow**
para rodar uma vez manualmente e conferir se o primeiro número aparece certo.

## Se algo quebrar

O script `scripts/fetch_snapshot.py` sempre imprime um erro claro na aba
**Actions** (clicando na execução que falhou) explicando o que aconteceu —
o mais comum é o Amplitude ter mudado o formato de resposta do gráfico,
o que exigiria um ajuste pequeno na função `extract_totals`.
