"""
Busca o snapshot mensal de engajamento da STLFLIX direto no Amplitude
e adiciona ao histórico (data/history.json).

Como funciona:
- Usa a "Chart Query API" do Amplitude, que devolve exatamente os mesmos
  números que aparecem no dashboard visual (o mesmo que você já usa hoje:
  "STLFLIX Engaj - Snapshot").
- Isso evita recalcular a lógica de "2 ações" na mão e ter números
  divergentes do que o time já está acostumado a ver no Amplitude.
- Roda automaticamente todo dia 1 do mês (via GitHub Actions), buscando
  o mês anterior (fechado).

Variáveis de ambiente necessárias (configuradas como "Secrets" no GitHub):
- AMPLITUDE_API_KEY
- AMPLITUDE_SECRET_KEY
- AMPLITUDE_CHART_ID   (o ID do gráfico, está na URL do dashboard)
"""

import os
import sys
import json
import calendar
from datetime import date
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

DATA_FILE = Path(__file__).parent.parent / "data" / "history.json"


def previous_month_range(today: date):
    """Retorna (primeiro_dia, ultimo_dia) do mês fechado anterior a hoje."""
    first_of_this_month = today.replace(day=1)
    last_day_prev_month = first_of_this_month.fromordinal(
        first_of_this_month.toordinal() - 1
    )
    first_day_prev_month = last_day_prev_month.replace(day=1)
    return first_day_prev_month, last_day_prev_month


def fetch_chart_data(api_key: str, secret_key: str, chart_id: str, start: date, end: date):
    url = f"https://amplitude.com/api/3/chart/{chart_id}/query"
    params = {
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
    }
    resp = requests.get(
        url,
        params=params,
        auth=HTTPBasicAuth(api_key, secret_key),
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def extract_totals(raw: dict):
    """
    Extrai os dois totais do payload do Amplitude:
    - logged_in_users: total do segmento 1 (All Users, planActive=True)
    - engaged_users: total do segmento 2 (engagement_action_stlflix_v2 >= 2)

    OBS: o formato exato do JSON pode variar. Se o Amplitude mudar o
    formato de resposta, esta função pode precisar de ajuste — o erro
    abaixo vai indicar isso claramente em vez de gravar número errado.
    """
    try:
        series = raw["data"]["series"]
        # cada série é uma lista de valores por período; como o gráfico
        # é mensal, pegamos a soma (deve ter 1 valor por mês solicitado)
        totals = [sum(s) if isinstance(s, list) else s for s in series]
        if len(totals) < 2:
            raise ValueError(f"Esperava 2 séries (All Users + segmento), veio {len(totals)}")
        logged_in_users = totals[0]
        engaged_users = totals[1]
        return int(logged_in_users), int(engaged_users)
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(
            f"Formato de resposta do Amplitude inesperado: {e}\n"
            f"Payload recebido: {json.dumps(raw)[:1000]}"
        )


def load_history():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []


def save_history(history):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def main():
    api_key = os.environ.get("AMPLITUDE_API_KEY")
    secret_key = os.environ.get("AMPLITUDE_SECRET_KEY")
    chart_id = os.environ.get("AMPLITUDE_CHART_ID")

    missing = [
        name
        for name, val in [
            ("AMPLITUDE_API_KEY", api_key),
            ("AMPLITUDE_SECRET_KEY", secret_key),
            ("AMPLITUDE_CHART_ID", chart_id),
        ]
        if not val
    ]
    if missing:
        print(f"ERRO: faltam variáveis de ambiente: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    today = date.today()
    start, end = previous_month_range(today)
    month_key = start.strftime("%Y-%m")

    print(f"Buscando snapshot de {start} até {end} (mês: {month_key})...")

    history = load_history()
    if any(row["month"] == month_key for row in history):
        print(f"Mês {month_key} já existe no histórico. Nada a fazer.")
        return

    raw = fetch_chart_data(api_key, secret_key, chart_id, start, end)
    logged_in_users, engaged_users = extract_totals(raw)
    engagement_rate = round(engaged_users / logged_in_users, 4) if logged_in_users else 0

    row = {
        "month": month_key,
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "logged_in_users": logged_in_users,
        "engaged_users": engaged_users,
        "engagement_rate": engagement_rate,
        "computed_at": today.isoformat(),
    }

    history.append(row)
    history.sort(key=lambda r: r["month"])
    save_history(history)

    print(f"OK: {month_key} -> {engaged_users}/{logged_in_users} = {engagement_rate:.1%}")


if __name__ == "__main__":
    main()
