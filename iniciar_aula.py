import argparse, os, threading, webbrowser
import uvicorn
parser=argparse.ArgumentParser(description='Laboratório das Poções: painel do professor')
parser.add_argument('--turma',default='padrao',help='Código da turma, por exemplo 91')
args=parser.parse_args()
os.environ['POCOES_TURMA']=args.turma
from servidor.main import ADMIN_TOKEN, CLASS_ID
print('Iniciando turma:', CLASS_ID)
threading.Timer(1.5,lambda:webbrowser.open('http://127.0.0.1:8765/professor?chave='+ADMIN_TOKEN)).start()
uvicorn.run('servidor.main:app',host='0.0.0.0',port=8765)
