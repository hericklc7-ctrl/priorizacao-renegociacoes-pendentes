# Clientes com renegociação pendente: maiores valores

Análise em **Python + DuckDB** que responde a uma pergunta prática de operações de cobrança:

> Entre os clientes que fecharam uma negociação nos últimos dias, **quais ainda estão com a renegociação pendente e têm os maiores saldos?**

O notebook lê os logs de ligações de um discador (vários arquivos Parquet), cruza com o log de carga da carteira e entrega uma lista ordenada por saldo, com telefone de contato, para a equipe priorizar o acompanhamento.

> ⚠️ **Todos os dados deste repositório são fictícios.** Foram gerados por [`src/gerar_dados_sinteticos.py`](src/gerar_dados_sinteticos.py) com a mesma estrutura dos arquivos de um cenário real. Os valores abaixo servem só para mostrar o funcionamento e **não representam nenhuma empresa ou cliente**.

---

## Como funciona

```
 logs de ligações (Parquet, vários arquivos)
        │   DuckDB: view com leitura por glob + union_by_name
        ▼
 negociações dos últimos 9 dias nas campanhas "extra"
        │   qualificação = "Negociação incluída agora"
        ▼
 cruzamento com o log de carga da carteira (CSV)
        │   situação = RN_PENDENTE
        ▼
 ranking por saldo total  ──►  CONTA · TELEFONE · SALDO_TOTAL · DIAS_ATRASO_REAL
```

## Exemplo de resultado (dados fictícios)

Execução com data de referência 17/10/2026:

| Etapa | Resultado |
|---|---|
| Ligações do mês (arquivos Parquet) | 42.000 |
| Negociações nas campanhas EXTRA_1 e EXTRA_2 (últimos 9 dias) | 284 registros · 267 contas distintas |
| Contas encontradas no log de carga | 250 |
| Contas em `RN_PENDENTE` | 158 |

Início da lista final, ordenada por saldo:

| CONTA | TELEFONE | SALDO_TOTAL | DIAS_ATRASO_REAL |
|---|---|---:|---:|
| 66272859 | 00904974235 | 6.952,20 | 80 |
| 49871096 | 00937408320 | 5.239,51 | 71 |
| 64274899 | 00998356843 | 4.765,69 | 283 |
| 74326827 | 00954540377 | 3.329,49 | 308 |
| 60147110 | 00950973363 | 3.013,33 | 730 |

Os números mudam conforme o dia da execução, porque a janela é relativa à data atual (`CURRENT_DATE`).

## Tecnologias

- **Python 3.10+**
- **DuckDB**: consulta Parquet com SQL, sem servidor de banco de dados
- **pandas**: cruzamento e tratamento dos dados
- **Jupyter**: análise passo a passo

## Como rodar

```bash
# 1. Clonar e entrar na pasta
git clone https://github.com/<seu-usuario>/priorizacao-renegociacoes-pendentes.git
cd priorizacao-renegociacoes-pendentes

# 2. Ambiente virtual e dependências
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Gerar os dados fictícios (pasta data/)
python src/gerar_dados_sinteticos.py

# 4. Abrir o notebook e executar as células
jupyter lab notebooks/priorizacao_renegociacoes_pendentes.ipynb
```

O gerador usa a data de hoje como referência. Para reproduzir uma data específica, use `--data-ref AAAA-MM-DD` (e ajuste o notebook, que usa `CURRENT_DATE`).

## Estrutura do repositório

```
├── notebooks/
│   └── priorizacao_renegociacoes_pendentes.ipynb   # a análise
├── src/
│   └── gerar_dados_sinteticos.py                   # gerador de dados fictícios
├── data/                                           # dados gerados (ignorados pelo Git)
├── requirements.txt
└── LICENSE
```

## Detalhes técnicos

- **Leitura por glob.** A view `lig` lê todos os arquivos Parquet do mês de uma vez, e o DuckDB consulta sem carregar tudo na memória do pandas.
- **`union_by_name=True`.** Os arquivos nem sempre têm as mesmas colunas; o DuckDB as une pelo nome em vez de falhar.
- **Datas como texto.** O discador grava `dd/mm/aaaa` como texto; `TRY_STRPTIME` converte e devolve `NULL` (em vez de erro) se houver data inválida.
- **Filtro tolerante.** `TRIM` e `ILIKE` evitam perder registros por espaços ou diferença de maiúsculas na qualificação.
- **Saldo como texto.** O log de carga traz o saldo com vírgula decimal (`"1234,56"`); a conversão para `float` acontece antes da ordenação, para não ordenar alfabeticamente.

## Privacidade

Dados de clientes e informações internas de empresas não pertencem a um repositório público. Por isso:

- o gerador cria telefones com DDD `00`, que não existe no Brasil, então nenhum número coincide com uma pessoa real;
- colunas que a análise não usa (como CPF) não são geradas;
- nomes de campanhas e assessorias são genéricos;
- `data/` e `saida/` estão no `.gitignore`.

## Limitações conhecidas e próximos passos

- **Conta repetida no resultado.** Se um cliente tem mais de uma negociação na janela, o `merge` final repete a conta (no exemplo acima, 158 clientes viram 173 linhas). Manter só a negociação mais recente de cada conta resolveria.
- **Virada de mês.** O padrão `*MM-AAAA.parquet` lê só o mês atual; se a janela de 9 dias cruza a virada, as ligações do mês anterior ficam de fora.
- **Critério de prioridade.** Hoje é só o saldo. Combinar com score de pagamento ou histórico de promessas tende a melhorar a ordem.
- **Automação.** Transformar o notebook em script agendado, entregando a lista todo dia.

## Autor

