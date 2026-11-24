# Laboratório das Poções v0.8.2 — revisão corretiva

## Correções
1. Missão 4 registra a letra A/B/C no diário, inclusive A (índice zero).
2. Atualização do painel preserva a anotação em edição.
3. Estudantes são apresentados com pseudônimo estável (Alquimista-XXXXXX); a API administrativa permite associar um apelido.
4. Escape HTML corrigido para apóstrofos.
5. Servidor disponibiliza `/index.html` para o cache PWA. Service workers exigem HTTPS ou localhost, não HTTP no IP LAN.
6. Testes JS atualizados e testes de servidor incluídos.
7. `python iniciar_aula.py --turma 91` cria banco e sala específicos da turma. Execute uma turma por vez na porta 8765.

## Pedagogia
Missão 4: A 2V1A sem reposição = 33,33%; B 5V3A sem reposição = 35,71%; C 5V3A com reposição = 39,0625%. Previsões das Missões 2–4 agora exigem erro máximo de 2 pontos percentuais, com opções mais finas. Cada retirada nas Missões 1–4 é anunciada por região persistente para leitor de tela.

## Instalação
`python -m pip install -r servidor/requirements.txt`
`python iniciar_aula.py --turma 91`
Abra o endereço do painel mostrado no terminal. Para turma 92, encerre a anterior e execute `python iniciar_aula.py --turma 92`.

## Limites
Não foi acrescentada árvore interativa nem elementos lúdicos novos. O PWA em celulares requer hospedagem HTTPS; na rede local HTTP a página pode funcionar, mas o service worker não é permitido. Ainda requer teste de navegação e acessibilidade com aparelhos reais.
