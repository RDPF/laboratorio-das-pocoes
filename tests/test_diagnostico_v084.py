"""Regression tests of individual feedback, including legacy and missing data."""
import importlib
import os
import pathlib
import sys
import tempfile

from fastapi.testclient import TestClient

from servidor.diagnostico import evaluate_attempt, summarize_student, BEST_PLAN


def sample(mission, score, details, id='r1'):
    return {'id': id, 'mission': mission, 'score': score, 'details': details, 'received': 1, 'at': '2026-11-06T15:00:00-03:00', 'student': 'student-17'}


def test_six_missions_reconstruct_scores():
    rows = [
        sample(1, 100, {'jar': 'C', 'prediction': 8, 'reason': 'no', 'history': ['red']*8+['blue']*2},'r1'),
        sample(2, 100, {'jar': 'A', 'prediction': 44, 'reason': 'a'},'r2'),
        sample(3, 100, {'jar': 'B', 'prediction': 36, 'reason': 'a'},'r3'),
        sample(4, 100, {'strategy': 'C', 'prediction': 39, 'reason': 'a'},'r4'),
        sample(5, 100, {'initial': 30, 'final': 50, 'reason': 'a', 'observations': [{'n':10,'red':5}, {'n':30,'red':13}, {'n':100,'red':45}]},'r5'),
        sample(6, 100, {'plan': list(BEST_PLAN), 'estimate': 20, 'reason': 'a'},'r6'),
    ]
    e = {r['id']: evaluate_attempt(r) for r in rows}
    assert [e[r['id']]['score_consistent'] for r in rows] == [True] * 6
    assert all(sum(c['maximum'] for c in e[r['id']]['criteria']) == 100 for r in rows)
    assert e['r5']['criteria'][0]['source'] == 'inferido_da_nota'
    assert 'não registrada' in e['r5']['warnings'][0]
    summary = summarize_student(rows, e)
    assert len(summary['missions']) == 6
    assert summary['missions'][5]['latest_score'] == 100


def test_real_errors_and_missing_information():
    incorrect = sample(3, 10, {'jar': 'A', 'prediction': 30, 'reason': 'c'},'wrong3')
    ev = evaluate_attempt(incorrect)
    assert ev['score_consistent'] is True
    assert [x['status'] for x in ev['criteria']] == ['incorreto', 'incorreto', 'incorreto', 'certo']
    summary = summarize_student([incorrect], {incorrect['id']: ev})
    assert any(f['concept']=='Dependência' and f['kind']=='retomada' for f in summary['findings'])
    # Legacy record: no prediction or interpretation; absence is not wrong.
    old=sample(4, 80, {'strategy': 'C'}, 'legacy4')
    ev=evaluate_attempt(old)
    assert ev['criteria'][1]['status']=='nao_verificavel'
    assert ev['score_consistent'] is None
    # M5 with no final: never assign points based solely on score.
    mystery=sample(5, 100, {'reason':'a', 'observations':[{'n':10,'red':4},{'n':30,'red':13},{'n':100,'red':39}]}, 'old5')
    ev=evaluate_attempt(mystery)
    assert ev['criteria'][0]['status']=='nao_verificavel'
    assert ev['criteria'][0]['expected'].startswith('Até 10')
    # Detected mismatch does not become a pedagogical classification.
    mismatched=sample(2, 0, {'jar':'A','prediction':44,'reason':'a'},'mismatch')
    ev=evaluate_attempt(mismatched)
    assert ev['score_consistent'] is False
    assert len(ev['warnings'])==1
    findings=summarize_student([mismatched], {mismatched['id']:ev})['findings']
    assert all(x['kind']!='retomada' for x in findings)


def test_authenticated_individual_report_and_existing_notes():
    old={key:os.environ.get(key) for key in ('POCOES_TURMA','POCOES_DB','POCOES_STATE')}
    try:
        with tempfile.TemporaryDirectory() as temp:
            os.environ.update(POCOES_TURMA='84',POCOES_DB=str(pathlib.Path(temp)/'pocoes.sqlite3'),POCOES_STATE=str(pathlib.Path(temp)/'room.json'))
            sys.modules.pop('servidor.main',None)
            mod=importlib.import_module('servidor.main')
            with TestClient(mod.app) as c:
                assert c.get('/api/student-report',params={'student':'s1'}).status_code==403
                assert c.get('/api/student-report',params={'chave':mod.ADMIN_TOKEN,'student':'s1'}).status_code==404
                assert c.post('/api/student-profile',json={'room':mod.ROOM,'student':'s1','alias':'Nº 17'}).status_code==200
                result=c.get('/api/student-report',params={'chave':mod.ADMIN_TOKEN,'student':'s1'})
                assert result.status_code==200
                assert result.json()['summary']['missions'][0]['attempts']==0
                for payload in [
                    {'id':'a', 'mission':3,'score':10,'details':{'jar':'A','prediction':30,'reason':'c'}},
                    {'id':'b', 'mission':2,'score':100,'details':{'jar':'A','prediction':44,'reason':'a'}},
                    {'id':'c', 'mission':5,'score':100,'details':{'initial':30,'final':50,'reason':'a','observations':[{'n':10,'red':5},{'n':30,'red':16},{'n':100,'red':49}]}},
                ]:
                    assert c.post('/api/submit',json={'room':mod.ROOM,'student':'s1','events':[payload]}).status_code==200
                assert c.post('/api/teacher-note',params={'chave':mod.ADMIN_TOKEN},json={'student':'s1','concept':'Dependência','level':'em_desenvolvimento','note':'Rever o segundo sorteio.'}).status_code==200
                data=c.get('/api/teacher-data',params={'chave':mod.ADMIN_TOKEN}).json()
                assert set(data['evaluations'])=={'a','b','c'}
                report=c.get('/api/student-report',params={'chave':mod.ADMIN_TOKEN,'student':'s1'}).json()
                assert report['alias']=='Nº 17'
                assert len(report['records'])==3
                assert report['evaluations']['a']['criteria'][0]['status']=='incorreto'
                assert report['evaluations']['b']['score_consistent'] is True
                assert report['evaluations']['c']['criteria'][0]['source']=='inferido_da_nota'
                assert report['notes'][0]['note']=='Rever o segundo sorteio.'
                assert any(f['concept']=='Dependência' for f in report['summary']['findings'])
                assert c.get('/professor',params={'chave':mod.ADMIN_TOKEN}).status_code==200
                panel=c.get('/professor',params={'chave':mod.ADMIN_TOKEN}).text
                assert 'Ficha individual de aprendizagem' in panel
                assert 'download-individual' in panel
                # Other students cannot be included in the selected report.
                assert c.post('/api/student-profile',json={'room':mod.ROOM,'student':'s2','alias':'Nº 18'}).status_code==200
                assert not any(r['student']=='s2' for r in report['records'])
    finally:
        for k, v in old.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
        sys.modules.pop('servidor.main',None)
