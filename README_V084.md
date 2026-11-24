# Laboratório das Poções v0.8.4 — diagnóstico individual do professor

Versão construída diretamente sobre a **v0.8.3**. O jogo dos estudantes foi preservado **sem alterações** nos arquivos HTML, CSS, JavaScript, imagem e service worker. Mantêm-se as seis missões, as mesmas probabilidades, pontuações e o sistema de identificação por pseudônimo (escolhido ou gerado).

## O que muda no painel do professor

A terceira aba, **Avaliação e Diagnóstico**, agora contém uma **Ficha individual de aprendizagem**. Ao selecionar o estudante, é possível consultar:

- As seis missões, com número de tentativas e nota da tentativa mais recente.
- Acertos, erros e critérios sem evidência direta, **separados**.
- O histórico de **todas** as tentativas daquele estudante; cada linha possui **Ver respostas**.
- Para cada tentativa: o que o estudante respondeu, o esperado pela regra matemática, o resultado do critério, o total de pontos e a justificativa da correção.
- Pistas de retomada ligadas às respostas registradas na **última tentativa de cada missão**.
- Exportação da ficha individual em JSON (inclui registros e anotações docentes) e da correção em CSV (compatível com Excel/LibreOffice).

As outras duas abas — Descobertas da Turma e Laboratório Estatístico — continuam disponíveis. As anotações pedagógicas manuais do professor permanecem no banco SQLite, não são alteradas pela correção automática e continuam editáveis.

### Quatro situações distinguíveis

1. **Acerto verificado:** há resposta no registro e o cálculo confere com a regra da v0.8.3.
2. **Erro verificado:** há resposta no registro e ela não satisfaz a regra.
3. **Resultado inferido da nota:** na Missão 5, a composição oculta não foi gravada; o painel consegue identificar se a estimativa recebeu 40 pontos a partir da nota, quando existem dados suficientes, mas não descobre qual era a probabilidade real do frasco.
4. **Dado insuficiente / divergência:** uma resposta não foi registrada, o formato é antigo ou a pontuação diverge dos critérios reconstruídos. O painel **não inventa** uma resposta nem transforma a divergência em diagnóstico de dificuldade.

As probabilidades e tolerâncias são exatamente as do código v0.8.3. A pontuação dos sorteios aleatórios **não** entra na avaliação matemática; as missões registradas ganham pontos fixos pela conclusão.

## Como executar no Windows / Miniforge

Na pasta extraída do ZIP:

```powershell
conda activate labprob
python -m pip install -r servidor\requirements.txt
python iniciar_aula.py --turma 91
```

Abra a URL administrativa completa apresentada no terminal. Na aba **Avaliação e Diagnóstico**, escolha um pseudônimo em **Ficha individual de aprendizagem**. Veja os critérios por missão, consulte o histórico e, se desejar, exporte JSON/CSV. A mesma seleção de estudante controla os campos de observação docente.

## Reaproveitar os registros da v0.8.3

Encerre o servidor antigo e copie, para a pasta **raiz** da v0.8.4, os dois arquivos correspondentes à turma:

- `pocoes_turma_91.sqlite3`
- `pocoes_sala_91.json`

Se usava a turma padrão (sem `--turma`), os nomes são `pocoes_turma.sqlite3` e `pocoes_sala.json`. Não renomeie a turma nem misture bancos de turmas diferentes. Faça uma cópia de segurança antes de mover. O servidor utiliza as tabelas SQLite já existentes; a v0.8.4 **não exige migração destrutiva nem altera tentativas antigas**.

## Limites e cuidados de interpretação

- A Missão 5 não salva a probabilidade verdadeira do recipiente; não se pode reconstruir retroativamente o erro exato da estimativa. O painel declara a limitação.
- Algumas tentativas antigas podem não conter `details` suficientes; elas aparecem como não verificáveis. Não são automaticamente tratadas como respostas erradas.
- Os rótulos de "retomada" são **indícios associados a decisões observadas**, e não diagnóstico conclusivo de proficiência ou dificuldade de aprendizagem.
- A correção retrata a regra das missões na v0.8.3. Caso existam registros provenientes de versões antigas cujas regras eram diferentes, o painel aponta divergências para conferência docente, em vez de reescrever notas.
- Pseudônimos são escolhidos pelo estudante; podem se repetir. O código curto apresentado junto ao nome diferencia identidades no mesmo painel.
- O acesso ao painel e às APIs de diagnóstico continua protegido pela chave administrativa da sala. O servidor usa HTTP local: não o exponha diretamente à internet.

## Validação técnica

- Suítes JavaScript herdadas, sem mudança de código do aluno.
- Testes do servidor e identidade v0.8.2/v0.8.3.
- Testes novos `tests/test_diagnostico_v084.py`: os seis critérios de pontuação, erros verificáveis, registros ausentes, divergências, segurança da API, persistência de anotações e isolamento entre estudantes.
- Teste visual de interação do painel em Chromium, com as respostas da API fornecidas por uma camada de transporte simulada, devido ao bloqueio de navegação HTTP local no ambiente de testes.

**Teste presencial ainda necessário:** celulares e notebook na rede escolar, atualização simultânea, usabilidade com pseudônimos reais, comportamento da impressão e acessibilidade com leitores de tela.
