"""
Gera dados 100% FICTÍCIOS para rodar o projeto sem expor nenhuma informação real.

Arquivos criados em `data/`:
  - ligacoes_semN_MM-AAAA.parquet
        Log de ligações do discador dos últimos 20 dias, um arquivo a cada ~5 dias
        (o último do mês tem uma coluna a mais, para demonstrar `union_by_name`).
        Se a janela cruza a virada do mês, os arquivos do mês anterior também são
        criados: o padrão de leitura do notebook os ignora, como na análise original.
  - LOG_CARGA_DDMMAAAA.csv
        Foto diária da carteira de cobrança (separador ';', decimal com vírgula).

Cuidados com privacidade:
  - Não há CPF, nome de cliente nem nome de operador real (a análise não usa).
  - Telefones começam com DDD "00", que não existe no Brasil: nunca coincidem
    com um número real.
  - Nomes de campanha, assessorias e lojas são genéricos.

A data de referência padrão é HOJE, para que o notebook (que usa CURRENT_DATE,
como a análise original) encontre dados recentes sempre que for executado.

Uso:
    python src/gerar_dados_sinteticos.py
    python src/gerar_dados_sinteticos.py --data-ref 2026-10-17 --seed 42
"""
from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# campanha -> probabilidade de aparecer numa ligação
CAMPANHAS = {
    "COB_14A30": 0.14,
    "COB_31A60": 0.14,
    "COB_61A180": 0.12,
    "COB_PREVENTIVO": 0.10,
    "COB_RECEPTIVO": 0.04,
    "COB_EXTRA_1": 0.20,
    "COB_EXTRA_2": 0.18,
    "COB_EXTRA_3": 0.08,
}
QUALIFICACOES = [
    "Sem contato",
    "Caixa postal",
    "Número errado",
    "Recado com terceiros",
    "Promessa de pagamento",
    "Negociação incluída agora",
]
# Probabilidades por qualificação (mesma ordem de QUALIFICACOES).
# Campanhas "extra" concentram mais negociações.
P_QUALIF_EXTRA = np.array([0.55, 0.22, 0.05, 0.07, 0.08, 0.03])
P_QUALIF_ROTINA = np.array([0.60, 0.22, 0.05, 0.07, 0.05, 0.015])

LIGACOES_POR_DIA = 3000


def telefone_ficticio(rng: np.random.Generator, n: int) -> np.ndarray:
    """DDD '00' não existe: o número nunca pertence a alguém de verdade."""
    return np.array([f"009{x:08d}" for x in rng.integers(0, 10**8, size=n)])


def gerar_carteira(rng: np.random.Generator, n_contas: int) -> pd.DataFrame:
    contas = rng.choice(np.arange(1_000_000, 90_000_000), size=n_contas, replace=False)
    dias = np.minimum(rng.gamma(shape=1.6, scale=180, size=n_contas).astype(int), 1500)
    saldo = np.clip(rng.lognormal(mean=6.4, sigma=1.0, size=n_contas), 50, 15_000).round(2)

    faixa = pd.cut(
        dias,
        bins=[-1, 30, 90, 180, 365, 10**6],
        labels=["FASE_01", "FASE_02", "FASE_03", "FASE_04", "FASE_05"],
    ).astype(str)

    return pd.DataFrame(
        {
            "CONTA": contas,
            "ASSESSORIA_COBRANCA": rng.choice(["ASSESSORIA_A", "ASSESSORIA_B", "INTERNA"], n_contas),
            "DIAS_ATRASO_REAL": dias,
            "FAIXA_ATRASO": faixa,
            "SITUACAO": rng.choice(
                ["DEVEDOR", "RN_PENDENTE", "RENEGOCIACAO"], n_contas, p=[0.55, 0.25, 0.20]
            ),
            "LOJA": rng.integers(1, 401, n_contas),
            "PRODUTO_CLIENTE": rng.choice(
                ["CARTAO", "CREDIARIO", "EMPRESTIMO"], n_contas, p=[0.5, 0.3, 0.2]
            ),
            # Formato do sistema de origem: texto com vírgula decimal
            "SALDO_TOTAL": [f"{v:.2f}".replace(".", ",") for v in saldo],
        }
    )


def gerar_ligacoes(
    rng: np.random.Generator,
    carteira: pd.DataFrame,
    dias: list[date],
    n_fora_da_carteira: int = 300,
) -> pd.DataFrame:
    # Universo de contas = carteira + algumas contas que NÃO estão na carteira
    # (simula contas já baixadas/encerradas, para testar a checagem de qualidade).
    fora = np.arange(90_000_001, 90_000_001 + n_fora_da_carteira)
    universo = np.concatenate([carteira["CONTA"].to_numpy(), fora])
    tel_conta = telefone_ficticio(rng, len(universo))

    pos_pendentes = np.flatnonzero((carteira["SITUACAO"] == "RN_PENDENTE").to_numpy())
    pos_outros = np.flatnonzero((carteira["SITUACAO"] != "RN_PENDENTE").to_numpy())
    pos_fora = np.arange(len(carteira), len(universo))

    campanhas = list(CAMPANHAS)
    p_camp = np.array(list(CAMPANHAS.values()))
    quadros = []

    for dia in dias:
        n = LIGACOES_POR_DIA
        camp = rng.choice(campanhas, n, p=p_camp)
        eh_extra = np.char.find(camp.astype(str), "EXTRA") >= 0

        qualif = np.where(
            eh_extra,
            rng.choice(QUALIFICACOES, n, p=P_QUALIF_EXTRA / P_QUALIF_EXTRA.sum()),
            rng.choice(QUALIFICACOES, n, p=P_QUALIF_ROTINA / P_QUALIF_ROTINA.sum()),
        )
        eh_negociacao = qualif == "Negociação incluída agora"

        # Escolha da conta: negociações tendem a vir de contas RN_PENDENTE,
        # mas nem todas (realismo) e algumas nem estão na carteira.
        pos = rng.integers(0, len(carteira), n)
        origem = rng.choice(["pend", "outros", "fora"], n, p=[0.60, 0.34, 0.06])
        pos = np.where(eh_negociacao & (origem == "pend"), rng.choice(pos_pendentes, n), pos)
        pos = np.where(eh_negociacao & (origem == "outros"), rng.choice(pos_outros, n), pos)
        pos = np.where(eh_negociacao & (origem == "fora"), rng.choice(pos_fora, n), pos)

        telefone = tel_conta[pos]
        troca = rng.random(n) < 0.08  # algumas ligações usam telefone alternativo
        telefone = np.where(troca, telefone_ficticio(rng, n), telefone)

        segundos = rng.integers(8 * 3600, 20 * 3600, n)
        hora = [f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}" for s in segundos]

        conexao = np.select(
            [qualif == "Sem contato", qualif == "Caixa postal"],
            ["Não atendida", "Caixa postal"],
            default="Atendida",
        )

        quadros.append(
            pd.DataFrame(
                {
                    "DATA": dia.strftime("%d/%m/%Y"),
                    "HORA": hora,
                    "AGENTE": [f"AGENTE_{i:02d}" for i in rng.integers(1, 31, n)],
                    "CAMPANHA": camp,
                    "LISTA": [c.replace("COB_", "") for c in camp],
                    "TELEFONE": telefone,
                    "CONEXAO": conexao,
                    "QUALIFICACAO": qualif,
                    "IDCONTATO_": universo[pos].astype(str),  # texto, como no sistema real
                }
            )
        )
    return pd.concat(quadros, ignore_index=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--data-ref", default=date.today().isoformat(),
                    help="Data de referência AAAA-MM-DD (padrão: hoje)")
    ap.add_argument("--saida", default="data", help="Pasta de saída")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n-contas", type=int, default=6000)
    args = ap.parse_args()

    ref = date.fromisoformat(args.data_ref)
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    carteira = gerar_carteira(rng, args.n_contas)

    # Últimos 20 dias (de segunda a sábado) antes da data de referência,
    # agrupados por mês: cada mês vira arquivos ligacoes_<n>_MM-AAAA.parquet.
    dias = [ref - timedelta(days=i) for i in range(1, 21)]
    dias = sorted(d for d in dias if d.weekday() != 6)
    mes_ref = f"{ref:%m-%Y}"
    if not any(f"{d:%m-%Y}" == mes_ref for d in dias):
        raise SystemExit("Use uma data de referência a partir do dia 2 do mês.")

    por_mes: dict[str, list[date]] = {}
    for d in dias:
        por_mes.setdefault(f"{d:%m-%Y}", []).append(d)

    for mes, ds in por_mes.items():
        # blocos de ~5 dias: vários arquivos por mês, como um export diário/semanal
        blocos = [ds[i:i + 5] for i in range(0, len(ds), 5)]
        for n, bloco in enumerate(blocos, start=1):
            df = gerar_ligacoes(rng, carteira, bloco)
            if n == len(blocos) and mes == mes_ref:
                # coluna presente só no último arquivo -> demonstra union_by_name
                df["tipo_ligacao"] = rng.choice(["OUTBOUND", "INBOUND"], len(df), p=[0.9, 0.1])
            df.to_parquet(saida / f"ligacoes_sem{n}_{mes}.parquet", index=False)

    carteira.to_csv(saida / f"LOG_CARGA_{ref:%d%m%Y}.csv", sep=";", index=False)

    print(f"Dados fictícios gerados em '{saida}/' (data de referência: {ref:%d/%m/%Y}):")
    for p in sorted(saida.iterdir()):
        if p.name != ".gitkeep":
            print(f"  - {p.name} ({p.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
