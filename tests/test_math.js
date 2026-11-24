const fs=require('fs'),vm=require('vm'),assert=require('assert');
const s=fs.readFileSync(__dirname+'/../duas-gotas.js','utf8');
const ctx=vm.createContext({});vm.runInContext(fs.readFileSync(__dirname+'/../probability-core.js','utf8'),ctx);vm.runInContext(s,ctx);
function p(r,b,repl){return vm.runInContext(`dProbability({red:${r},blue:${b}},${repl})`,ctx)}
assert(Math.abs(p(3,2,true)-.36)<1e-12);
assert(Math.abs(p(3,2,false)-.3)<1e-12);
assert(Math.abs(p(4,3,true)-16/49)<1e-12);
assert(Math.abs(p(4,3,false)-2/7)<1e-12);
assert(Math.abs(p(5,4,false)-5/18)<1e-12);
for(let r=2;r<=10;r++)for(let b=1;b<=10;b++)assert(p(r,b,false)<p(r,b,true));
console.log('Probabilidades com e sem reposição: OK');
