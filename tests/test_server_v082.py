import os, tempfile, pathlib, importlib, sys
from fastapi.testclient import TestClient

def test_class_isolation():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ['POCOES_TURMA']='91';os.environ['POCOES_DB']=str(pathlib.Path(tmp)/'91.sqlite3');os.environ['POCOES_STATE']=str(pathlib.Path(tmp)/'91.json')
        sys.modules.pop('servidor.main',None)
        mod=importlib.import_module('servidor.main')
        with TestClient(mod.app) as c:
            assert c.get('/index.html').status_code==200
            assert c.get('/professor').status_code==403
            event={'room':mod.ROOM,'student':'uuid-student','events':[{'id':'one','mission':4,'score':80,'details':{'strategy':'C'}}]}
            assert c.post('/api/submit',json=event).status_code==200
            result=c.get('/api/teacher-data',params={'chave':mod.ADMIN_TOKEN}).json()
            assert len(result['records'])==1
            assert result['aliases']['uuid-student'].startswith('Alquimista-')
            assert c.post('/api/student-alias',params={'chave':mod.ADMIN_TOKEN},json={'student':'uuid-student','alias':'Coruja-17'}).status_code==200
            assert c.get('/api/teacher-data',params={'chave':mod.ADMIN_TOKEN}).json()['aliases']['uuid-student']=='Coruja-17'
        os.environ['POCOES_TURMA']='92';os.environ['POCOES_DB']=str(pathlib.Path(tmp)/'92.sqlite3');os.environ['POCOES_STATE']=str(pathlib.Path(tmp)/'92.json')
        sys.modules.pop('servidor.main',None)
        mod2=importlib.import_module('servidor.main')
        assert mod2.ROOM!=mod.ROOM
        with TestClient(mod2.app) as c:
            assert c.get('/api/teacher-data',params={'chave':mod2.ADMIN_TOKEN}).json()['records']==[]
