"""Servidor local v0.8: sala persistente, validação de registros e evidências."""
import io, json, os, secrets, sqlite3, socket, time, hashlib, re
from pathlib import Path
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, Field
import qrcode
from .diagnostico import evaluate_attempt, summarize_student

ROOT=Path(__file__).resolve().parent.parent
CLASS_ID=os.environ.get('POCOES_TURMA','padrao').strip()
if not re.fullmatch(r'[A-Za-z0-9_-]{1,32}',CLASS_ID):
    raise ValueError('Identificador da turma inválido (use letras, números, _ ou -)')
SUFFIX='' if CLASS_ID=='padrao' else '_'+CLASS_ID
DB=Path(os.environ.get('POCOES_DB',str(ROOT/('pocoes_turma'+SUFFIX+'.sqlite3'))))
STATE=Path(os.environ.get('POCOES_STATE',str(ROOT/('pocoes_sala'+SUFFIX+'.json'))))
app=FastAPI(title='Laboratório das Poções · Turma v0.8.4')

def get_room_state():
    if STATE.exists():
        try:
            data=json.loads(STATE.read_text(encoding='utf8'))
            if isinstance(data.get('room'),str) and isinstance(data.get('token'),str) and len(data['room'])==6 and len(data['token'])>20:
                return data
        except (ValueError,OSError):pass
    data={'room':secrets.token_hex(3).upper(),'token':secrets.token_urlsafe(32)}
    STATE.parent.mkdir(parents=True,exist_ok=True)
    # Do not regenerate if a valid room already exists; store local-only credentials.
    with STATE.open('w',encoding='utf8') as f:json.dump(data,f)
    try:os.chmod(STATE,0o600)
    except OSError:pass
    return data

# Loaded on startup as well as import; stable across restarts.
ROOM_STATE=get_room_state()
ROOM=ROOM_STATE['room'];ADMIN_TOKEN=ROOM_STATE['token']

@contextmanager
def conn():
    c=sqlite3.connect(DB,timeout=10)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('CREATE TABLE IF NOT EXISTS attempts (id TEXT PRIMARY KEY, room TEXT NOT NULL, student TEXT NOT NULL, mission INTEGER NOT NULL, score INTEGER NOT NULL, at TEXT, details TEXT NOT NULL, received INTEGER NOT NULL)')
    c.execute('CREATE TABLE IF NOT EXISTS student_aliases (room TEXT NOT NULL, student TEXT NOT NULL, alias TEXT NOT NULL, PRIMARY KEY(room,student))')
    c.execute('CREATE TABLE IF NOT EXISTS teacher_notes (room TEXT NOT NULL, student TEXT NOT NULL, concept TEXT NOT NULL, level TEXT NOT NULL, note TEXT NOT NULL, updated INTEGER NOT NULL, PRIMARY KEY(room,student,concept))')
    try:yield c;c.commit()
    finally:c.close()

class Event(BaseModel):
    id:str=Field(min_length=1,max_length=100)
    at:str=Field(default='',max_length=50)
    mission:int=Field(ge=1,le=6)
    score:int=Field(ge=0,le=100)
    details:dict=Field(default_factory=dict)
class Submission(BaseModel):
    room:str=Field(min_length=6,max_length=6)
    student:str=Field(min_length=1,max_length=100)
    alias:str=Field(default='',max_length=40)
    events:list[Event]=Field(min_length=1,max_length=100)

def validate_alias(raw):
    value=' '.join(raw.strip().split())
    if not value or len(value)>32 or any(ord(c)<32 or ord(c)==127 or c in '<>' for c in value):
        raise HTTPException(422,'Identificador inválido: use 1 a 32 caracteres sem símbolos HTML.')
    return value

class StudentProfile(BaseModel):
    room:str=Field(min_length=6,max_length=6)
    student:str=Field(min_length=1,max_length=100)
    alias:str=Field(min_length=1,max_length=40)

@app.post('/api/student-profile')
def register_student(item:StudentProfile):
    if item.room!=ROOM:raise HTTPException(403,'Sala não reconhecida.')
    alias=validate_alias(item.alias)
    with conn() as c:
        c.execute('INSERT INTO student_aliases VALUES (?,?,?) ON CONFLICT(room,student) DO UPDATE SET alias=excluded.alias',(ROOM,item.student,alias))
    return {'ok':True,'alias':alias}

@app.on_event('startup')
def startup():
    with conn():pass
    print('\nPAINEL DO PROFESSOR: http://127.0.0.1:8765/professor?chave='+ADMIN_TOKEN)
    print('TURMA: '+CLASS_ID+' | SALA PERSISTENTE: '+ROOM+'\n')

def check(token):
    if not secrets.compare_digest(token or '',ADMIN_TOKEN):raise HTTPException(403,'Acesso restrito ao professor')

def ip_address():
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try:s.connect(('192.0.2.1',1));return s.getsockname()[0]
    except OSError:return '127.0.0.1'
    finally:s.close()

def class_url():return f'http://{ip_address()}:8765/?sala={ROOM}'

@app.get('/')
def index():return FileResponse(ROOT/'index.html')
@app.get('/index.html')
def index_file():return FileResponse(ROOT/'index.html')
@app.post('/api/submit')
def submit(s:Submission):
    if s.room!=ROOM:raise HTTPException(403,'Sala não reconhecida. Solicite ao professor o QR Code atualizado.')
    for e in s.events:
        if len(json.dumps(e.details,ensure_ascii=False))>16000:raise HTTPException(413,'Registro maior que 16 KB')
    alias=validate_alias(s.alias) if s.alias else None
    with conn() as c:
        if alias:
            c.execute('INSERT INTO student_aliases VALUES (?,?,?) ON CONFLICT(room,student) DO UPDATE SET alias=excluded.alias',(ROOM,s.student,alias))
        for e in s.events:
            c.execute('INSERT OR IGNORE INTO attempts VALUES (?,?,?,?,?,?,?,?)',(e.id,ROOM,s.student,e.mission,e.score,e.at,json.dumps(e.details,ensure_ascii=False),int(time.time())))
    return {'ok':True,'received':len(s.events)}

@app.get('/api/summary')
def summary(chave:str=''):
    check(chave)
    with conn() as c:
        count=c.execute('SELECT COUNT(DISTINCT student),COUNT(*) FROM attempts WHERE room=?',(ROOM,)).fetchone()
        rows=c.execute('SELECT mission,COUNT(*),ROUND(AVG(score),1),MAX(score) FROM attempts WHERE room=? GROUP BY mission ORDER BY mission',(ROOM,)).fetchall()
        details=c.execute('SELECT mission,details FROM attempts WHERE room=?',(ROOM,)).fetchall()
    choices={str(i):{} for i in range(1,7)}
    experiments={str(i):{'trials':0,'successes':0,'red':0,'blue':0} for i in range(1,7)}
    for mission,raw in details:
        try:d=json.loads(raw)
        except ValueError:continue
        key=str(mission)
        decision=d.get('jar') if mission in (1,2,3) else d.get('strategy') if mission==4 else None
        if isinstance(decision,str) and decision in ('A','B','C'):
            choices[key][decision]=choices[key].get(decision,0)+1
        history=d.get('history')
        if mission==1 and isinstance(history,list):
            for x in history:
                if x in ('red','blue'):experiments[key][x]+=1;experiments[key]['trials']+=1
        elif mission in (2,3,4) and isinstance(history,list):
            for x in history:
                if isinstance(x,dict) and isinstance(x.get('draws'),list) and len(x['draws'])==2:
                    experiments[key]['trials']+=1
                    experiments[key]['successes']+=int(x['draws']==['red','red'])
        elif mission==5:
            obs=d.get('observations')
            if isinstance(obs,list) and obs:
                last=obs[-1]
                if isinstance(last,dict):
                    experiments[key]['trials']+=int(last.get('n',0))
                    experiments[key]['red']+=int(last.get('red',0))
                    experiments[key]['blue']+=int(last.get('blue',0))
    return {'room':ROOM,'students':count[0],'attempts':count[1],'missions':[{'mission':r[0],'attempts':r[1],'average':r[2],'best':r[3]} for r in rows],'choices':choices,'experiments':experiments}

class TeacherNote(BaseModel):
    student:str=Field(min_length=1,max_length=100)
    concept:str=Field(min_length=1,max_length=60)
    level:str=Field(pattern='^(observacao|em_desenvolvimento|evidencia|nao_avaliado)$')
    note:str=Field(default='',max_length=2000)

@app.get('/api/teacher-data')
def teacher_data(chave:str=''):
    check(chave)
    with conn() as c:
        rows=c.execute('SELECT id,student,mission,score,at,details,received FROM attempts WHERE room=? ORDER BY received,id',(ROOM,)).fetchall()
        notes=c.execute('SELECT student,concept,level,note,updated FROM teacher_notes WHERE room=? ORDER BY updated DESC',(ROOM,)).fetchall()
    records=[]
    for r in rows:
        try: detail=json.loads(r[5])
        except (ValueError,TypeError): detail={}
        records.append({'id':r[0],'student':r[1],'mission':r[2],'score':r[3],'at':r[4],'details':detail,'received':r[6]})
    with conn() as c:
        aliases=dict(c.execute('SELECT student,alias FROM student_aliases WHERE room=?',(ROOM,)).fetchall())
    for student in {r['student'] for r in records}:
        if student not in aliases:
            aliases[student]='Alquimista-'+hashlib.sha256((ROOM+':'+student).encode()).hexdigest()[:6].upper()
    codes={student:hashlib.sha256((ROOM+':'+student).encode()).hexdigest()[:6].upper() for student in aliases}
    evaluations={r['id']:evaluate_attempt(r) for r in records}
    return {'room':ROOM,'records':records,'aliases':aliases,'codes':codes,'evaluations':evaluations,'notes':[dict(zip(('student','concept','level','note','updated'),n)) for n in notes]}

@app.get('/api/student-report')
def student_report(chave:str='',student:str=''):
    """Individual evidence report, restricted to the teacher's session."""
    check(chave)
    if not student or len(student)>100:raise HTTPException(422,'Informe um estudante válido.')
    collection=teacher_data(chave)
    known=student in collection['aliases']
    if not known:raise HTTPException(404,'Estudante não encontrado nesta turma.')
    selected=[r for r in collection['records'] if r['student']==student]
    evaluations={r['id']:collection['evaluations'][r['id']] for r in selected}
    notes=[n for n in collection['notes'] if n['student']==student]
    summary=summarize_student(selected,evaluations)
    return {'schema':'pocoes.student-report.v084','room':ROOM,'student':student,
            'alias':collection['aliases'][student],'code':collection['codes'][student],
            'records':selected,'evaluations':evaluations,'summary':summary,'notes':notes,
            'limitations':[
                'As conclusões são indícios descritivos, não prova de domínio ou dificuldade permanente.',
                'Na Missão 5, a probabilidade real do frasco oculto não foi gravada na v0.8.3; a correção da estimativa só pode ser inferida pela pontuação quando todos os componentes estão disponíveis.',
                'Registros de versões anteriores ou incompletos podem não reproduzir a pontuação: divergências são identificadas, não corrigidas silenciosamente.'
            ]}

class StudentAlias(BaseModel):
    student:str=Field(min_length=1,max_length=100)
    alias:str=Field(min_length=1,max_length=40)

@app.post('/api/student-alias')
def student_alias(item:StudentAlias,chave:str=''):
    check(chave)
    with conn() as c:
        if not c.execute('SELECT 1 FROM attempts WHERE room=? AND student=?',(ROOM,item.student)).fetchone():
            raise HTTPException(404,'Estudante não encontrado nesta turma')
        c.execute('INSERT INTO student_aliases VALUES (?,?,?) ON CONFLICT(room,student) DO UPDATE SET alias=excluded.alias',(ROOM,item.student,item.alias.strip()))
    return {'ok':True}

@app.post('/api/teacher-note')
def teacher_note(item:TeacherNote,chave:str=''):
    check(chave)
    with conn() as c:
        c.execute('INSERT INTO teacher_notes VALUES (?,?,?,?,?,?) ON CONFLICT(room,student,concept) DO UPDATE SET level=excluded.level,note=excluded.note,updated=excluded.updated',(ROOM,item.student,item.concept,item.level,item.note,int(time.time())))
    return {'ok':True}

@app.get('/api/export')
def export(chave:str=''):
    check(chave)
    with conn() as c:
        rows=c.execute('SELECT id,room,student,mission,score,at,details FROM attempts WHERE room=? ORDER BY received',(ROOM,)).fetchall()
    return JSONResponse({'room':ROOM,'schema':'pocoes.class.v08','attempts':[{**dict(zip(('id','room','student','mission','score','at','details'),r)),'details':json.loads(r[6])} for r in rows]},headers={'Content-Disposition':'attachment; filename="turma-pocoes-v08.json"'})

@app.get('/api/qr')
def qr(chave:str=''):
    check(chave)
    im=qrcode.make(class_url());b=io.BytesIO();im.save(b,format='PNG')
    return Response(b.getvalue(),media_type='image/png')

@app.get('/professor')
def teacher(chave:str=''):
    check(chave)
    html=(ROOT/'servidor'/'professor.html').read_text(encoding='utf8')
    return HTMLResponse(html.replace('__TOKEN__',ADMIN_TOKEN).replace('__URL__',class_url()).replace('__ROOM__',ROOM))

@app.get('/{filename}')
def static(filename:str):
    if filename not in ('style.css','game.js','duas-gotas.js','estrategias.js','misterio.js','campanha.js','mestre.js','pedagogia.js','coletivo.js','probability-core.js','manifest.webmanifest','sw.js'):raise HTTPException(404)
    return FileResponse(ROOT/filename)
@app.get('/assets/{filename}')
def asset(filename:str):
    if filename!='capa.webp':raise HTTPException(404)
    return FileResponse(ROOT/'assets'/filename)
