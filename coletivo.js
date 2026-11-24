"use strict";
/* v0.8.3 — identificação opcional, por turma, sem cadastro e com fila por aluno. */
const ROOM_KEY='pocoes-sala-v08', CLIENT_KEY='pocoes-aluno-v07', QUEUE_KEY='pocoes-fila-v08';
const OLD_QUEUE_KEY='pocoes-fila-v07', PROFILE_KEY='pocoes-identidades-v083';
function localRead(k){try{return localStorage.getItem(k)}catch{return null}}
function localWrite(k,v){try{localStorage.setItem(k,v);return true}catch{return false}}
function newStudentId(){return typeof crypto!=='undefined'&&typeof crypto.randomUUID==='function'?crypto.randomUUID():'aluno-'+Date.now()+'-'+Math.random().toString(36).slice(2);}
function getLegacyStudentId(){let id=localRead(CLIENT_KEY);if(!id){id=newStudentId();localWrite(CLIENT_KEY,id);}return id;}
function readProfiles(){try{const o=JSON.parse(localRead(PROFILE_KEY)||'{}');return o&&typeof o==='object'&&!Array.isArray(o)?o:{}}catch{return {}}}
function profileRoom(room){return room||'individual';}
function makeAutoAlias(student){const slug=String(student).replace(/[^0-9a-z]/gi,'').slice(-6).toUpperCase();return 'Alquimista-'+(slug||'000001');}
function initialProfile(room){const key=profileRoom(room),profiles=readProfiles(),existing=profiles[key];if(existing&&typeof existing.student==='string'&&existing.student){return {student:existing.student,alias:String(existing.alias||makeAutoAlias(existing.student)),confirmed:!!existing.confirmed,mode:existing.mode||'auto'};}
 // Migrate the v0.8.2 device ID in the first classroom: earlier attempts remain associated.
 const student=Object.keys(profiles).length?newStudentId():getLegacyStudentId();
 return {student,alias:makeAutoAlias(student),confirmed:false,mode:'auto'};
}
function storeProfile(){const profiles=readProfiles();profiles[profileRoom(collective.room)]={student:collective.student,alias:collective.alias,confirmed:collective.confirmed,mode:collective.mode};return localWrite(PROFILE_KEY,JSON.stringify(profiles));}
function readQueue(){try{const q=JSON.parse(localRead(QUEUE_KEY)||'[]');return Array.isArray(q)?q:[]}catch{return []}}
function writeQueue(q){if(!localWrite(QUEUE_KEY,JSON.stringify(q))){syncState='Armazenamento cheio: exporte seu diário';return false;}return true;}
let syncState='';
const requestedRoom=new URLSearchParams(location.search).get('sala');
const room=requestedRoom||localRead(ROOM_KEY)||(typeof sessionStorage!=='undefined'?sessionStorage.getItem('pocoes-sala-v07'):'')||'';
const p=initialProfile(room);
const collective={room,student:p.student,alias:p.alias,confirmed:p.confirmed,mode:p.mode,busy:false,profileBusy:false,profileDirty:true};
if(collective.room){localWrite(ROOM_KEY,collective.room);try{sessionStorage.setItem('pocoes-sala-v07',collective.room)}catch{}}
// Legacy queue did not store student per event; attach the original device identity at migration.
try{const old=JSON.parse(localRead(OLD_QUEUE_KEY)||'[]');if(Array.isArray(old)&&old.length){const merged=readQueue(),legacy=getLegacyStudentId();for(const row of old){if(!merged.some(x=>x.id===row.id))merged.push({...row,room:row.room||collective.room,student:row.student||legacy});}if(writeQueue(merged))localStorage.removeItem(OLD_QUEUE_KEY);}}catch{}
function identityLabel(){return collective.alias||makeAutoAlias(collective.student)}
function identityBadge(){const b=document.getElementById('identity-badge');if(!b)return;b.textContent='🧪 '+identityLabel();b.title='Consultar ou alterar meu identificador';b.setAttribute('aria-label','Meu identificador: '+identityLabel()+'. Alterar identificação');}
function identityModal(open){const modal=document.getElementById('identity-modal');if(!modal)return;modal.hidden=!open;if(open){const input=document.getElementById('identity-name');input.value=collective.confirmed&&collective.mode==='custom'?collective.alias:'';document.getElementById('identity-code').textContent='Identificador automático disponível: '+makeAutoAlias(collective.student);document.getElementById('identity-cancel').hidden=!collective.confirmed;document.getElementById('identity-error').textContent='';input.focus();}else{identityBadge();document.getElementById('identity-badge')?.focus();}}
function normalizeAlias(value){const s=String(value).normalize('NFC').trim().replace(/\s+/g,' ');if(!s||s.length>32||/[\u0000-\u001f\u007f<>]/.test(s))return null;return /^\d{1,3}$/.test(s)?'Nº '+s:s;}
function setIdentity(value,mode){const alias=mode==='auto'?makeAutoAlias(collective.student):normalizeAlias(value);if(!alias){document.getElementById('identity-error').textContent='Use 1 a 32 caracteres: um pseudônimo ou número de chamada, sem símbolos HTML.';return false;}
 const before={alias:collective.alias,mode:collective.mode,confirmed:collective.confirmed};collective.alias=alias;collective.mode=mode;collective.confirmed=true;
 if(!storeProfile()){Object.assign(collective,before);document.getElementById('identity-error').textContent='Não foi possível guardar a identificação neste navegador.';return false;}
 collective.profileDirty=true;identityModal(false);identityBadge();collectiveRegister();return true;
}
function identityInit(){const badge=document.getElementById('identity-badge');if(badge)badge.addEventListener('click',()=>identityModal(true));document.getElementById('identity-accept')?.addEventListener('click',()=>setIdentity(document.getElementById('identity-name').value,'custom'));document.getElementById('identity-auto')?.addEventListener('click',()=>setIdentity('', 'auto'));document.getElementById('identity-cancel')?.addEventListener('click',()=>identityModal(false));document.getElementById('identity-name')?.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();setIdentity(e.currentTarget.value,'custom');}});identityBadge();if(collective.room&&!collective.confirmed)identityModal(true);else if(collective.room)collectiveRegister();}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',identityInit);else identityInit();
async function collectiveRegister(){if(!collective.room||!collective.confirmed||collective.profileBusy||!collective.profileDirty||!/^https?:$/.test(location.protocol))return;
 collective.profileBusy=true;const alias=collective.alias,student=collective.student,room=collective.room;
 try{const res=await fetch('/api/student-profile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({room,student,alias})});if(!res.ok){syncState='Identificação ainda não registrada no servidor';return;}if(alias===collective.alias&&student===collective.student&&room===collective.room)collective.profileDirty=false;}
 catch{syncState='Sem conexão: identificação pendente';}
 finally{collective.profileBusy=false;}
}
function collectiveSend(row){if(!collective.room)return;const q=readQueue();if(!q.some(x=>x.id===row.id)){q.push({...row,room:collective.room,student:collective.student,alias:collective.alias});if(!writeQueue(q))return;}collectiveSync();}
async function collectiveSync(){
 if(collective.busy||!/^https?:$/.test(location.protocol))return;
 if(collective.profileDirty&&!collective.profileBusy)await collectiveRegister();
 const q=readQueue();if(!q.length){if(collective.room)syncState=collective.profileDirty?'Identificação pendente':'Todos os registros enviados';return;}
 collective.busy=true;
 try{const first=q.find(x=>(x.room||collective.room)===collective.room&&(x.student||getLegacyStudentId())===collective.student)||q.find(x=>(x.room||collective.room)===collective.room);
  if(!first){syncState='Há registros de outra turma preservados; entre naquela sala para enviá-los';return;}
  const sendingRoom=first.room||collective.room,student=first.student||getLegacyStudentId();
  if(!sendingRoom){syncState='Registros antigos sem sala: exporte seu diário';return;}
  const batch=q.filter(x=>(x.room||collective.room)===sendingRoom&&(x.student||getLegacyStudentId())===student).slice(0,50);
  const alias=sendingRoom===collective.room&&student===collective.student?collective.alias:(batch.at(-1)?.alias||'');
  const events=batch.map(({room,student,alias,...event})=>event);
  const res=await fetch('/api/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({room:sendingRoom,student,alias,events})});
  if(!res.ok){let error='HTTP '+res.status;try{const d=await res.json();error=typeof d.detail==='string'?d.detail:error;}catch{}syncState=res.status===403?'Sala não reconhecida: procure o professor; dados preservados':`Servidor recusou envio (${error}); dados preservados`;return;}
  const sent=new Set(batch.map(x=>x.id));writeQueue(readQueue().filter(x=>!sent.has(x.id)));
  syncState=readQueue().length?'Enviando registros pendentes':'Todos os registros enviados';
 }catch{syncState='Sem conexão: registros aguardam sincronização';}
 finally{collective.busy=false;}
}
function collectiveHubControls(){const host=document.querySelector('.campaign-panel');if(!host)return;const el=document.createElement('div');el.className='connection-pill';el.setAttribute('role','status');el.textContent=collective.room?`📡 Sala ${collective.room} · ${identityLabel()} · ${readQueue().length} pendente(s). ${syncState}`:`📱 ${identityLabel()} · modo individual offline`;host.after(el);
 if(collective.room){const b=document.createElement('button');b.className='secondary';b.textContent='Sincronizar resultados';b.onclick=async()=>{await collectiveSync();el.textContent=`📡 Sala ${collective.room} · ${identityLabel()} · ${readQueue().length} pendente(s). ${syncState}`;};el.after(b);}}
if(/^https?:$/.test(location.protocol))setInterval(collectiveSync,8000);
