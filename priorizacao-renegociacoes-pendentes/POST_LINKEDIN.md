# Rascunho de post para o LinkedIn

> Troque o que está entre [colchetes] e ajuste o texto para soar como você. O LinkedIn esconde tudo depois das ~3 primeiras linhas ("ver mais"), então a abertura precisa funcionar sozinha.
> Sugestão de imagem: um print da tabela final do notebook (com os dados fictícios).

---

## Versão principal

Numa operação de cobrança, quem a equipe deveria acompanhar primeiro?

Publiquei no GitHub uma análise que responde isso: entre os clientes que fecharam uma negociação nos últimos dias, quais ainda estão com a renegociação pendente e têm os maiores saldos.

Como funciona:

→ DuckDB lê vários arquivos Parquet de ligações de uma vez, com SQL, sem subir banco de dados
→ Filtra as negociações recentes das campanhas de reforço
→ Cruza com a foto diária da carteira para ver a situação de cada conta
→ Entrega a lista ordenada por saldo, já com o telefone de contato

Uma parte que me deu trabalho: **como publicar isso sem expor nada real.** Dado de cliente e informação interna não vão para o GitHub. Então escrevi um gerador de dados fictícios com a mesma estrutura dos arquivos originais, com telefones de DDD inexistente, para qualquer pessoa rodar o projeto do zero.

Detalhes que parecem pequenos e quebram análises: o saldo chegando como texto com vírgula decimal (ordena alfabeticamente se ninguém converter) e datas gravadas como texto.

Código e README: [link do repositório]

Você trabalha com cobrança, CRM ou análise de operações? Me conta como a sua equipe decide quem contatar primeiro.

#Python #DuckDB #AnaliseDeDados #DataAnalytics #Portfolio

---

## Frases de abertura alternativas

1. "Ordenar clientes pelo maior saldo parece simples. Até o saldo chegar como texto com vírgula e a lista sair em ordem alfabética."
2. "Publiquei meu primeiro projeto de portfólio de dados. A parte mais difícil não foi o código: foi decidir o que NÃO podia ir para o GitHub."
3. "Dá para analisar milhões de linhas em Parquet com SQL, sem banco de dados. Mostro como no meu novo projeto."

## Dicas

- Publique em dia útil, de manhã, e responda os primeiros comentários rápido.
- Coloque o link no texto, ou no primeiro comentário se preferir manter o leitor na plataforma.
- Fixe o repositório (*pin*) no seu perfil do GitHub.
