"""Identity registration is room-scoped and does not require a finished mission."""
import os
import sys
import importlib
import pathlib
import tempfile
from fastapi.testclient import TestClient


def test_student_registration_and_legacy_submissions():
    old={key:os.environ.get(key) for key in ('POCOES_TURMA','POCOES_DB','POCOES_STATE')}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ.update(POCOES_TURMA='83',POCOES_DB=str(pathlib.Path(tmp)/'83.sqlite3'),POCOES_STATE=str(pathlib.Path(tmp)/'83.json'))
            sys.modules.pop('servidor.main',None)
            mod=importlib.import_module('servidor.main')
            with TestClient(mod.app) as c:
                assert c.post('/api/student-profile',json={'room':mod.ROOM,'student':'student-1','alias':'Coruja-17'}).status_code==200
                assert c.post('/api/student-profile',json={'room':mod.ROOM,'student':'student-2','alias':'Coruja-17'}).status_code==200
                data=c.get('/api/teacher-data',params={'chave':mod.ADMIN_TOKEN}).json()
                assert data['records']==[]
                assert data['aliases']['student-1']=='Coruja-17'
                assert data['aliases']['student-2']=='Coruja-17'
                assert data['codes']['student-1']!=data['codes']['student-2']
                assert c.post('/api/student-profile',json={'room':'BADBAD','student':'student-3','alias':'Lobo'}).status_code==403
                for invalid in ('','<script>','a'*33):
                    assert c.post('/api/student-profile',json={'room':mod.ROOM,'student':'student-3','alias':invalid}).status_code==422
                assert c.get('/api/teacher-data').status_code==403
                # Older v0.8.2 clients do not send alias: they must continue working.
                payload={'room':mod.ROOM,'student':'legacy-v082','events':[{'id':'old1','mission':1,'score':60,'details':{'jar':'C'}}]}
                assert c.post('/api/submit',json=payload).status_code==200
                data=c.get('/api/teacher-data',params={'chave':mod.ADMIN_TOKEN}).json()
                assert data['aliases']['legacy-v082'].startswith('Alquimista-')
                # Identity can accompany a queued submission when the profile endpoint was unreachable.
                payload={'room':mod.ROOM,'student':'student-4','alias':'Nº 17','events':[{'id':'e1','mission':4,'score':80,'details':{'strategy':'C'}}]}
                assert c.post('/api/submit',json=payload).status_code==200
                assert c.post('/api/submit',json=payload).status_code==200
                data=c.get('/api/teacher-data',params={'chave':mod.ADMIN_TOKEN}).json()
                assert data['aliases']['student-4']=='Nº 17'
                assert len(data['records'])==2
                # Update display name, keep permanent student ID and previous attempts.
                assert c.post('/api/student-profile',json={'room':mod.ROOM,'student':'student-4','alias':'Falcão-3'}).status_code==200
                data=c.get('/api/teacher-data',params={'chave':mod.ADMIN_TOKEN}).json()
                assert data['aliases']['student-4']=='Falcão-3'
                assert len([r for r in data['records'] if r['student']=='student-4'])==1
                assert 'Falcão-3' in c.get('/professor',params={'chave':mod.ADMIN_TOKEN}).text or 'studentName' in c.get('/professor',params={'chave':mod.ADMIN_TOKEN}).text
                room_before=mod.ROOM
            # Room remains stable after reimport/restart using same files.
            sys.modules.pop('servidor.main',None)
            mod2=importlib.import_module('servidor.main')
            assert mod2.ROOM==room_before
            with TestClient(mod2.app) as c:
                data=c.get('/api/teacher-data',params={'chave':mod2.ADMIN_TOKEN}).json()
                assert data['aliases']['student-4']=='Falcão-3'
    finally:
        for k,v in old.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
        sys.modules.pop('servidor.main',None)
