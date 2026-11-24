# Laboratório das Poções v0.8.4

**Campanha completa de seis missões e painel docente em três abas.**

## Abrir o jogo individual

Abra `ABRIR_OFFLINE.html`. É o **mesmo arquivo dos estudantes da v0.8.3**, intencionalmente preservado byte a byte. Não exige servidor, conta ou conexão para o uso individual.

## Abrir o programa do professor

No Windows, extraia o ZIP, abra o Miniforge Prompt dentro da pasta e execute:

```powershell
conda activate labprob
python -m pip install -r servidor\requirements.txt
python iniciar_aula.py --turma 91
```

O endereço do painel aparece no terminal e normalmente abre automaticamente. O QR Code da sala permite acessar o jogo pelo celular quando houver rede local compatível.

### As três abas

1. **Descobertas da Turma:** apresentação dos dados experimentais e discussão matemática.
2. **Laboratório Estatístico:** frequências, estratégias separadas e intervalos de Wilson.
3. **Avaliação e Diagnóstico:** ficha individual com respostas e critérios de correção, histórico de tentativas, indícios pedagógicos e anotações docentes.

Leia `README_V084.md` para detalhes, limites da correção, uso dos arquivos SQLite da versão anterior e testes. Consulte `README_PAINEL_PROFESSOR.md` para instruções específicas do painel.

**Importante:** a nova ficha analisa os dados efetivamente registrados. Não inventa informações ausentes, como o recipiente oculto da Missão 5. As evidências não substituem a avaliação e a observação do professor.
