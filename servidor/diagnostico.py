"""Correção rastreável a partir dos registros v0.8.3.

Não reinterpreta resultados aleatórios como acertos. Não inventa dados ausentes;
na missão 5 a composição real não é salva pela aplicação dos estudantes.
Compatível com tentativas já gravadas no SQLite.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from math import isclose

NAMES = [
    'A Poção Rubra', 'Duas Gotas de Poder', 'O Ingrediente Desaparecido',
    'A Receita Mais Segura', 'O Recipiente Misterioso', 'O Mestre Alquimista'
]
JARS_SINGLE = {'A': (2, 3), 'B': (3, 2), 'C': (4, 1)}
JARS_DOUBLE = {'A': (2, 1), 'B': (5, 3), 'C': (3, 2)}
JARS_STRATEGY = {'A': (2, 1, False), 'B': (5, 3, False), 'C': (5, 3, True)}
ORDERS = (
    ({'id': 'A', 'red': 3, 'blue': 3, 'replacement': False, 'cost': 4},
     {'id': 'B', 'red': 3, 'blue': 1, 'replacement': True, 'cost': 5},
     {'id': 'C', 'red': 5, 'blue': 3, 'replacement': False, 'cost': 3}),
    ({'id': 'A', 'red': 2, 'blue': 1, 'replacement': True, 'cost': 4},
     {'id': 'B', 'red': 4, 'blue': 2, 'replacement': False, 'cost': 3},
     {'id': 'C', 'red': 3, 'blue': 1, 'replacement': False, 'cost': 5}),
)
MAX_BUDGET = 7


def pair(red, blue, replacement):
    n = red + blue
    return (red / n) * (red / n if replacement else (red - 1) / (n - 1))


def plan_probability(plan):
    return pair(**{k: v for k, v in ORDERS[0][plan[0]].items() if k in ('red','blue','replacement')}) * pair(**{k: v for k, v in ORDERS[1][plan[1]].items() if k in ('red','blue','replacement')})


def plan_cost(plan):
    return sum(ORDERS[i][v]['cost'] for i, v in enumerate(plan))


VALID_PLANS = [(i, j) for i in range(3) for j in range(3) if plan_cost((i, j)) <= MAX_BUDGET]
BEST_PLAN = max(VALID_PLANS, key=plan_probability)
BEST_PLAN_PROB = plan_probability(BEST_PLAN)


def percent(p):
    return f'{p * 100:.2f}'.replace('.', ',') + '%'


def option_text(option):
    return {'a': 'A', 'b': 'B', 'c': 'C', 'yes': 'Sim', 'no': 'Não', 'never': 'Não é possível'}.get(str(option), str(option))


def _number(value):
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _choice(value):
    return value if isinstance(value, str) and value in ('A', 'B', 'C') else None


def evaluate_attempt(record):
    """Return evidence + explicit epistemic limits for *one* stored attempt."""
    m = record.get('mission')
    d = record.get('details') if isinstance(record.get('details'), dict) else {}
    score = record.get('score')
    criteria, warnings = [], []

    def add(label, concept, answer, expected, correct, maximum, explanation='', source='registro', code=''):
        # correct must be True, False or None.
        status = 'certo' if correct is True else 'incorreto' if correct is False else 'nao_verificavel'
        criteria.append({
            'label': label, 'concept': concept, 'answer': str(answer) if answer is not None else 'Não registrado',
            'expected': str(expected) if expected is not None else 'Não disponível',
            'status': status, 'points': maximum if correct is True else 0 if correct is False else None,
            'maximum': maximum, 'source': source if correct is not None else 'ausente',
            'explanation': explanation, 'code': code,
        })

    if m == 1:
        jar = _choice(d.get('jar'))
        red = JARS_SINGLE[jar][0] if jar else None
        add('Escolha do frasco', 'Probabilidade simples', jar, 'C (4 vermelhas em 5; 80%)', jar == 'C' if jar else None,
            40, 'A maior probabilidade de obter uma gota vermelha é a do frasco C.', code='escolha')
        pred = _number(d.get('prediction'))
        expected = red * 2 if red is not None else None
        add('Previsão em 10 retiradas', 'Esperança e frequência', f'{int(pred)} de 10' if pred is not None else None,
            f'{expected} de 10 (valor esperado, não resultado garantido)' if expected is not None else None,
            pred == expected if pred is not None and expected is not None else None, 30,
            'A previsão pontuada é o valor esperado. O experimento pode produzir outro total.', code='previsao')
        reason = d.get('reason')
        add('Interpretação da variabilidade', 'Variabilidade amostral', option_text(reason) if reason is not None else None,
            'Não — dez novas retiradas podem produzir outro resultado (alternativa «no»).',
            reason == 'no' if reason is not None else None, 20,
            'A frequência observada não precisa coincidir com o valor esperado.', code='interpretacao')
        h = d.get('history')
        if isinstance(h, list):
            reds = sum(x == 'red' for x in h)
            supplementary = f'{reds} vermelhas em {len(h)} retiradas.'
        else: supplementary = 'Sequência de retiradas não registrada.'
    elif m in (2, 3):
        repl = m == 2
        probs = {key: pair(*JARS_DOUBLE[key], repl) for key in JARS_DOUBLE}
        best = max(probs, key=probs.get)
        jar = _choice(d.get('jar'))
        p = probs.get(jar)
        add('Escolha do frasco', 'Independência' if repl else 'Dependência', jar,
            f'{best} ({percent(probs[best])})', jar == best if jar else None, 40,
            'Compare P(VV) para cada recipiente, considerando a regra de reposição.', code='escolha')
        pred = _number(d.get('prediction'))
        add('Previsão de duas vermelhas', 'Probabilidade composta', percent(pred / 100) if pred is not None else None,
            f'{percent(p)} (tolerância ±2 pontos percentuais)' if p is not None else None,
            abs(pred - 100 * p) <= 2 + 1e-10 if pred is not None and p is not None else None, 30,
            'A previsão é avaliada em relação ao frasco que o estudante escolheu.', code='previsao')
        reason = d.get('reason')
        add('Interpretação da reposição', 'Independência' if repl else 'Dependência', option_text(reason) if reason is not None else None,
            'A — ' + ('a reposição restabelece a composição.' if repl else 'a retirada vermelha reduz a chance da próxima vermelha.'),
            reason == 'a' if reason is not None else None, 20,
            'A resposta indica o reconhecimento da constância ou alteração da segunda probabilidade.', code='interpretacao')
        supplementary = 'Seis preparações registradas; resultados aleatórios não alteram a nota.'
    elif m == 4:
        probs = {k: pair(*v) for k, v in JARS_STRATEGY.items()}
        best = max(probs, key=probs.get)
        chosen = _choice(d.get('strategy'))
        p = probs.get(chosen)
        add('Comparação de estratégias', 'Estratégias e reposição', chosen,
            f'{best} ({percent(probs[best])}; 5V+3A com reposição)',
            chosen == best if chosen else None, 40,
            'B e C têm a mesma composição; a regra de reposição determina a diferença.', code='escolha')
        pred = _number(d.get('prediction'))
        add('Previsão da estratégia', 'Probabilidade composta', percent(pred / 100) if pred is not None else None,
            f'{percent(p)} (tolerância ±2 pontos percentuais)' if p is not None else None,
            abs(pred - 100 * p) <= 2 + 1e-10 if pred is not None and p is not None else None, 30,
            'A previsão refere-se à estratégia efetivamente selecionada.', code='previsao')
        reason = d.get('reason')
        add('Justificativa da estratégia', 'Estratégias e reposição', option_text(reason) if reason is not None else None,
            'A — comparar ambas as retiradas, considerando a reposição.',
            reason == 'a' if reason is not None else None, 20,
            'Escolher só pela proporção inicial ou por seis sucessos não é justificativa suficiente.', code='interpretacao')
        supplementary = 'Seis preparações registradas; resultados aleatórios não alteram a nota.'
    elif m == 5:
        first = _number(d.get('initial'))
        final = _number(d.get('final'))
        reason = d.get('reason')
        quiz_ok = reason == 'a' if reason is not None else None
        # The old client only persisted the score, not the hidden population.
        # If the answer to the quiz was saved, the 40-point component can be
        # inferred algebraically from the exact scoring rule, but the true p
        # remains unrecoverable. Never claim direct verification of the target.
        inferred = None
        if final is not None and quiz_ok is not None and type(score) is int:
            residual = score - 30 - (30 if quiz_ok else 0)
            if residual in (0, 40): inferred = residual == 40
        add('Estimativa final', 'Inferência probabilística', f'{int(final)}%' if final is not None else None,
            'Até 10 pontos percentuais da probabilidade oculta (valor verdadeiro não registrado)',
            inferred, 40,
            'A situação de acerto foi reconstruída pela pontuação, não pela composição oculta, que falta no registro.',
            source='inferido_da_nota', code='estimativa')
        add('Interpretação da amostra', 'Variabilidade amostral', option_text(reason) if reason is not None else None,
            'A — a frequência de 100 retiradas estima, mas não garante a probabilidade verdadeira.',
            quiz_ok, 30, 'Uma amostra maior não torna a frequência obrigatoriamente exata.', code='interpretacao')
        obs = d.get('observations')
        valid = (isinstance(obs, list) and len(obs) == 3 and [o.get('n') for o in obs if isinstance(o, dict)] == [10, 30, 100])
        add('Investigação amostral', 'Frequência relativa', '10, 30 e 100 retiradas' if valid else None,
            'Etapas de 10, 30 e 100 retiradas', True if valid else None, 20,
            'As três observações acumuladas dão evidência da investigação.', code='experimento')
        supplementary = ('Hipótese inicial: ' + (f'{int(first)}%' if first is not None else 'não registrada') +
                         '; hipótese final: ' + (f'{int(final)}%' if final is not None else 'não registrada') +
                         '. Composição verdadeira indisponível nos registros v0.8.3.')
        warnings.append('Missão 5: composição real do frasco não registrada. Acerto da estimativa apenas inferido pela nota quando possível; valor verdadeiro e erro absoluto não podem ser reconstruídos.')
    elif m == 6:
        raw = d.get('plan')
        valid = (isinstance(raw, list) and len(raw) == 2 and all(type(i) is int and i in (0, 1, 2) for i in raw))
        chosen = tuple(raw) if valid else None
        p = plan_probability(chosen) if chosen is not None else None
        plan_txt = ' + '.join(ORDERS[i][j]['id'] for i,j in enumerate(chosen)) if chosen is not None else None
        optimal = chosen is not None and plan_cost(chosen) <= MAX_BUDGET and isclose(p, BEST_PLAN_PROB, abs_tol=1e-12)
        best_txt = ' + '.join(ORDERS[i][j]['id'] for i,j in enumerate(BEST_PLAN))
        add('Plano com orçamento', 'Otimização de probabilidades', plan_txt,
            f'{best_txt} ({percent(BEST_PLAN_PROB)}; custo {plan_cost(BEST_PLAN)} cristais)',
            optimal if chosen is not None else None, 40,
            'Duas probabilidades são multiplicadas, com custo total de até sete cristais.', code='escolha')
        pred = _number(d.get('estimate'))
        add('Previsão do plano', 'Probabilidade composta', percent(pred / 100) if pred is not None else None,
            f'{percent(p)} (tolerância ±10 pontos percentuais)' if p is not None else None,
            abs(pred - 100 * p) <= 10 + 1e-10 if pred is not None and p is not None else None, 30,
            'A avaliação preserva a tolerância usada pela Missão 6 da v0.8.3.', code='previsao')
        reason = d.get('reason')
        add('Interpretação de estratégia', 'Otimização de probabilidades', option_text(reason) if reason is not None else None,
            'A — maximizar a probabilidade conjunta respeitando o orçamento.',
            reason == 'a' if reason is not None else None, 20,
            'Fracasso em uma execução não prova que o plano é ruim.', code='interpretacao')
        supplementary = 'Duas encomendas sob um orçamento total de sete cristais.'
    else:
        return {'criteria': [], 'warnings': ['Missão desconhecida.'], 'score_consistent': None, 'reconstructed_score': None, 'supplementary': ''}

    # Completed missions award 10 points, without dependence on random outcomes.
    add('Conclusão da missão', 'Participação', 'Missão registrada como concluída',
        'Missão concluída', True, 10, 'Pontos automáticos pela conclusão.', source='registro', code='participacao')
    missing = any(c['points'] is None for c in criteria)
    reconstructed = sum(c['points'] for c in criteria) if not missing else None
    consistent = reconstructed == score if reconstructed is not None and type(score) is int else None
    if consistent is False:
        warnings.append('Pontuação gravada diverge da correção reconstituída. Verifique a versão original, migração ou integridade do registro; não se atribuiu diagnóstico automático.')
    return {
        'mission': m, 'score': score, 'criteria': criteria, 'reconstructed_score': reconstructed,
        'score_consistent': consistent, 'warnings': warnings, 'supplementary': supplementary,
        'source_version': 'regras_v0.8.3',
    }


QUESTIONS = {
    'Probabilidade simples': 'Como comparar a chance de vermelha em recipientes com composições diferentes?',
    'Esperança e frequência': 'O número esperado de vermelhas precisa ocorrer exatamente nas próximas dez retiradas?',
    'Independência': 'Por que a segunda probabilidade permanece a mesma quando a gota volta?',
    'Dependência': 'O que muda no denominador após retirar uma gota sem reposição?',
    'Probabilidade composta': 'Como se calcula a chance de duas vermelhas consecutivas?',
    'Estratégias e reposição': 'Como duas estratégias com o mesmo frasco podem produzir chances distintas?',
    'Inferência probabilística': 'O que os dados de 10, 30 e 100 retiradas permitem estimar?',
    'Variabilidade amostral': 'Uma frequência diferente da teórica significa erro na probabilidade?',
    'Frequência relativa': 'Como a frequência relativa muda quando aumentamos a amostra?',
    'Otimização de probabilidades': 'Qual plano maximiza a chance conjunta respeitando o orçamento?',
}


def summarize_student(records, evaluations):
    by_mission = defaultdict(list)
    for r in records:
        by_mission[r['mission']].append(r)
    overview = []
    for m in range(1, 7):
        rows = sorted(by_mission[m], key=lambda r: (r.get('received', 0), r.get('at',''), r['id']))
        latest = rows[-1] if rows else None
        overview.append({
            'mission': m, 'name': NAMES[m-1], 'attempts': len(rows),
            'latest_id': latest['id'] if latest else None,
            'latest_score': latest['score'] if latest else None,
            'latest_at': latest['at'] if latest else None,
        })
    findings = []
    # Only more recent attempt per mission to avoid over-weighting repetitions.
    latest = [max(rows, key=lambda r: (r.get('received',0), r.get('at',''), r['id'])) for rows in by_mission.values() if rows]
    incorrect = defaultdict(list)
    unknown = defaultdict(list)
    for r in latest:
        ev = evaluations[r['id']]
        for c in ev['criteria']:
            if c['code'] == 'participacao': continue
            if ev['score_consistent'] is False or c['source'] == 'inferido_da_nota':
                # Divergent score and indirect inference need teacher review,
                # not automatic pedagogical classification.
                unknown[c['concept']].append(r['mission'])
            elif c['status'] == 'incorreto': incorrect[c['concept']].append(r['mission'])
            elif c['status'] == 'nao_verificavel': unknown[c['concept']].append(r['mission'])
    for concept, missions in sorted(incorrect.items(), key=lambda item: (-len(item[1]), item[0])):
        findings.append({'concept': concept, 'kind': 'retomada',
                         'statement': 'Resposta diferente da esperada em ' + ', '.join('M' + str(i) for i in sorted(set(missions))) + '.',
                         'question': QUESTIONS.get(concept, 'Solicite que o estudante justifique sua resposta.'),
                         'missions': sorted(set(missions))})
    for concept, missions in sorted(unknown.items()):
        findings.append({'concept': concept, 'kind': 'dados_insuficientes',
                         'statement': 'Sem registro suficiente para verificar: ' + ', '.join('M' + str(i) for i in sorted(set(missions))) + '.',
                         'question': 'Observe a justificativa do estudante em uma nova atividade.', 'missions': sorted(set(missions))})
    if not latest:
        findings.append({'concept': 'Participação', 'kind': 'sem_tentativas',
                         'statement': 'Nenhuma missão concluída registrada para este pseudônimo.',
                         'question': 'Verifique se o estudante entrou na sala correta.', 'missions': []})
    return {'missions': overview, 'findings': findings,
            'scope': 'Evidências descritivas da tentativa mais recente em cada missão; não constituem diagnóstico definitivo.'}
