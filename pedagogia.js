"use strict";
const LEARN_KEY='pocoes-aprendizagem-v06';
const MISSION_NAMES=['A Poção Rubra','Duas Gotas de Poder','O Ingrediente Desaparecido','A Receita Mais Segura','O Recipiente Misterioso','O Mestre Alquimista'];
function learnRead(){try{const d=JSON.parse(localStorage.getItem(LEARN_KEY)||'[]');return Array.isArray(d)?d:[]}catch{return []}}
function learnWrite(rows){try{localStorage.setItem(LEARN_KEY,JSON.stringify(rows.slice(-600)))}catch{}}
function learningRecord(mission,score){
 const details={};try{
 if(mission===1){Object.assign(details,{jar:JARS[state.jar]?.id,prediction:state.pred,red:state.reds,draws:state.trial,history:state.history,reason:state.quiz,expected:JARS[state.jar]?.red*2});}
 else if(mission===2||mission===3){Object.assign(details,{jar:DOUBLE_JARS[duo.jar]?.id,prediction:duo.forecast,success:duo.success,draws:duo.round,history:duo.results,reason:duo.quiz});}
 else if(mission===4){Object.assign(details,{strategy:STRATEGIES[strat.choice]?.id,prediction:strat.estimate,history:strat.results,reason:strat.quiz});}
 else if(mission===5){Object.assign(details,{initial:mystery.firstEstimate,final:mystery.finalEstimate,red:mystery.red,draws:100,observations:mystery.observations,reason:mystery.quiz});}
 else if(mission===6){Object.assign(details,{plan:master.plan,estimate:master.estimate,history:master.draws,reason:master.quiz});}
 }catch{}
 const row={id:(crypto.randomUUID?crypto.randomUUID():Date.now()+'-'+Math.random()),at:new Date().toISOString(),mission,score,details};
 learnWrite([...learnRead(),row]);
 if(typeof collectiveSend==='function')collectiveSend(row);
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function learningSummary(rows=learnRead()){
 return MISSION_NAMES.map((name,i)=>{const r=rows.filter(x=>x.mission===i+1);const mean=r.length?r.reduce((a,x)=>a+x.score,0)/r.length:null;return {mission:i+1,name,attempts:r.length,mean,high:r.filter(x=>x.score>=70).length,best:r.length?Math.max(...r.map(x=>x.score)):null};});
}
function learningInsights(rows=learnRead()){
 const n=rows.length;if(!n)return ['Ainda não há tentativas concluídas. Jogue uma missão para gerar evidências.'];
 const notes=[];const low=learningSummary(rows).filter(x=>x.attempts&&x.mean<60);if(low.length)notes.push('Retomar em aula: '+low.map(x=>'Missão '+x.mission).join(', ')+'. As pontuações médias ficaram abaixo de 60/100.');
 const m23=rows.filter(x=>x.mission===2||x.mission===3);if(m23.length)notes.push('Dependência e reposição: '+m23.length+' registros nas Missões 2–3. Peça que comparem o segundo sorteio nos dois casos.');
 const m5=rows.filter(x=>x.mission===5);if(m5.length)notes.push('Amostragem: '+m5.length+' investigações concluídas. Discuta por que 100 retiradas não garantem frequência igual à probabilidade teórica.');
 notes.push('Indicadores descritivos, não diagnóstico individual: repetir a missão pode aumentar o número de tentativas e alterar as médias.');return notes;
}
function learningPage(){const rows=learnRead(),sum=learningSummary(rows),avg=rows.length?Math.round(rows.reduce((a,x)=>a+x.score,0)/rows.length):null;
 base(`<div class="card stack"><span class="eyebrow">Diário de descobertas · v0.8</span><h1>O que aprendemos?</h1><p>O relatório mostra decisões matemáticas e evolução por missão. Não é uma classificação por sorte.</p><div class="statgrid"><div class="stat"><strong>${rows.length}</strong><span>Tentativas</span></div><div class="stat"><strong>${sum.filter(x=>x.attempts).length}/6</strong><span>Missões exploradas</span></div><div class="stat"><strong>${avg===null?'—':avg+'/100'}</strong><span>Média das tentativas</span></div></div><h2>Missões e evidências</h2>${sum.map(x=>`<div class="learn-row"><div><strong>${x.mission}. ${x.name}</strong><small>${x.attempts} tentativa(s) · melhor ${x.best===null?'—':x.best+'/100'}</small></div><div class="learn-meter"><div style="width:${x.mean||0}%"></div></div><strong>${x.mean===null?'—':Math.round(x.mean)+'/100'}</strong></div>`).join('')}<h2>Pistas para investigar</h2>${learningInsights(rows).map(x=>`<div class="hint">${escapeHtml(x)}</div>`).join('')}<h2>Diário de tentativas</h2>${rows.length?`<div class="learn-history">${rows.slice(-12).reverse().map(x=>`<div><strong>Missão ${x.mission}</strong> · ${x.score}/100 <small>${new Date(x.at).toLocaleString('pt-BR')}</small></div>`).join('')}</div>`:'<p>Conclua uma missão para registrar a primeira evidência.</p>'}<div class="actions">${btn('export','Exportar CSV','secondary')}${btn('json','Exportar JSON','secondary')}</div>${btn('hub','Voltar às missões','ghost')}</div>`);
 $('export').onclick=()=>learningExport('csv');$('json').onclick=()=>learningExport('json');$('hub').onclick=missionHub;
}
function learningExport(format){const rows=learnRead();let body,mime,ext;if(format==='json'){body=JSON.stringify({schema:'pocoes.learning.v1',generatedAt:new Date().toISOString(),rows},null,2);mime='application/json';ext='json'}else{const fields=['id','at','mission','score','details'];body='\uFEFF'+fields.join(';')+'\n'+rows.map(x=>fields.map(k=>'"'+String(k==='details'?JSON.stringify(x.details):x[k]??'').replace(/"/g,'""')+'"').join(';')).join('\n');mime='text/csv;charset=utf-8';ext='csv'}const url=URL.createObjectURL(new Blob([body],{type:mime}));const a=document.createElement('a');a.href=url;a.download='pocoes-aprendizagem.'+ext;a.click();setTimeout(()=>URL.revokeObjectURL(url),500);}
