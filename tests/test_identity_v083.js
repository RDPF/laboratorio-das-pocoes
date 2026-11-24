'use strict';
const assert=require('assert'),fs=require('fs'),vm=require('vm');
const code=fs.readFileSync(__dirname+'/../coletivo.js','utf8');
function context(seed={}){
 const stored={...seed},listeners={},elems={};
 const get=id=>(elems[id]??={hidden:true,textContent:'',value:'',addEventListener(){},focus(){},setAttribute(){}});
 const ctx=vm.createContext({
  localStorage:{getItem:k=>stored[k]??null,setItem:(k,v)=>{stored[k]=String(v)},removeItem:k=>delete stored[k]},
  sessionStorage:{getItem(){return null},setItem(){}},
  location:{search:'?sala=ABC123',protocol:'https:'},
  document:{readyState:'loading',getElementById:get,addEventListener:(event,fn)=>{listeners[event]=fn},querySelector:()=>null},
  crypto:{randomUUID:()=> 'abcd1234-5678-9abc-def0-123456789abc'},
  URLSearchParams,Date,Math,JSON,Set,Promise,setInterval(){},
  fetch:async (url,opts)=>({ok:true,status:200,json:async()=>({ok:true}),url,opts}),
 });
 vm.runInContext(code,ctx);
 return {ctx,stored,elems,listeners};
}
(async()=>{
 const a=context();a.listeners.DOMContentLoaded();
 assert.strictEqual(a.elems['identity-modal'].hidden,false,'First room entry asks for identity');
 assert.strictEqual(vm.runInContext("normalizeAlias('  17  ')",a.ctx),'Nº 17');
 assert.strictEqual(vm.runInContext("normalizeAlias('<b>')",a.ctx),null);
 assert.strictEqual(vm.runInContext("normalizeAlias(' Coruja  17 ')",a.ctx),'Coruja 17');
 assert.strictEqual(vm.runInContext("setIdentity('17','custom')",a.ctx),true);
 assert.strictEqual(a.elems['identity-modal'].hidden,true);
 assert(a.elems['identity-badge'].textContent.includes('Nº 17'));
 const id=vm.runInContext('collective.student',a.ctx);
 vm.runInContext("collectiveSend({id:'record-1',mission:2,score:80,details:{jar:'A'}})",a.ctx);
 assert.strictEqual(JSON.parse(a.stored['pocoes-fila-v08'])[0].student,id,'Queued event retains author');
 await new Promise(r=>setImmediate(r));
 // Browser refresh reuses exactly the same student and nickname.
 const b=context(a.stored);b.listeners.DOMContentLoaded();
 assert.strictEqual(vm.runInContext('collective.student',b.ctx),id);
 assert.strictEqual(vm.runInContext('collective.alias',b.ctx),'Nº 17');
 assert.strictEqual(b.elems['identity-modal']?.hidden??true,true);
 vm.runInContext("setIdentity('Coruja-17','custom')",b.ctx);
 await new Promise(r=>setImmediate(r));
 assert.strictEqual(vm.runInContext('collective.student',b.ctx),id,'Rename must not split records');
 // Old classroom's queue must not block delivery from the current classroom.
 const old=[{id:'other',room:'AAAAAA',student:'old-student',mission:1,score:0,details:{}},{id:'current',room:'ABC123',student:id,alias:'Coruja-17',mission:2,score:80,details:{}}];
 b.stored['pocoes-fila-v08']=JSON.stringify(old);
 let requests=[];
 b.ctx.fetch=async (url,opts)=>{requests.push({url,payload:JSON.parse(opts.body)});return {ok:true,status:200,json:async()=>({ok:true})};};
 await vm.runInContext('collectiveSync()',b.ctx);
 assert(requests.some(r=>r.url==='/api/submit'&&r.payload.room==='ABC123'&&r.payload.student===id));
 assert.deepStrictEqual(JSON.parse(b.stored['pocoes-fila-v08']).map(x=>x.id),['other']);
 console.log('v0.8.3: identidade, persistência, renomeação, autoria da fila e turma ativa OK');
})().catch(e=>{console.error(e);process.exit(1)});
