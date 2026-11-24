# Painel do Professor — v0.8.4

A v0.8.4 preserva as duas primeiras abas da v0.8.3 e amplia a terceira. O jogo dos estudantes permanece inalterado.

## Aba 1 — Descobertas da Turma

Projeção dos dados agregados, escolhas por estratégia e questões para discussão após as seis missões.

## Aba 2 — Laboratório Estatístico

Análise por missão e estratégia, frequência relativa, intervalos de Wilson e histórico de retiradas quando disponível.

## Aba 3 — Avaliação e Diagnóstico

Selecione o estudante em **Ficha individual de aprendizagem**. As seis linhas mostram a última tentativa de cada missão (ou "Sem registro"). Clique em **Ver** para expandir a correção. O **Histórico completo** permite consultar também todas as tentativas anteriores, sem apagar ou substituir nenhuma nota.

Cada correção mostra os critérios da missão: resposta do estudante, resposta esperada, acerto/erro/não verificável, pontos e justificativa matemática. Um aviso é mostrado quando a nota gravada não confere com a reconstrução. Na Missão 5, o acerto da estimativa pode ser **inferido da pontuação**, mas a probabilidade verdadeira não foi gravada e não é reconstruída.

As **Pistas pedagógicas** destacam conceitos para retomada, com perguntas sugeridas baseadas nas respostas da tentativa mais recente de cada missão. Elas não substituem o diálogo com o estudante. Os campos tradicionais de **Registro do professor** continuam disponíveis com gravação persistente no SQLite.

Use **Exportar ficha JSON** para um relatório completo do estudante, incluindo observações docentes, ou **Exportar correções CSV** para tabulação.

## Preservar dados e separar turmas

Execute `python iniciar_aula.py --turma 91` e, para outra turma, reinicie com `--turma 92`. Cada turma possui sala e banco SQLite próprios. Para reutilizar dados anteriores, copie os arquivos correspondentes **com o servidor desligado** e mantenha o mesmo número de turma. Faça uma cópia de segurança antes da transferência.

## Limitações da análise

A Missão 5 guarda totais acumulados e estimativas, não a composição verdadeira do frasco. Dados ausentes ou de formatos antigos aparecem como não verificáveis. Rótulos de retomada correspondem somente às respostas registradas e não indicam diagnósticos definitivos de aprendizagem.
