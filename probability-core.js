"use strict";
/* Motor único para duas retiradas, com/sem reposição. */
const ProbabilityCore=Object.freeze({
  pair(red,blue,replacement){const n=red+blue;if(!Number.isInteger(red)||!Number.isInteger(blue)||red<0||blue<0||n<2)return 0;return (red/n)*(replacement?red/n:(red-1)/(n-1));},
  branches(red,blue,replacement){const n=red+blue;return [
    {first:'V',second:'V',probability:(red/n)*((red-(replacement?0:1))/(n-(replacement?0:1)))},
    {first:'V',second:'A',probability:(red/n)*(blue/(n-(replacement?0:1)))},
    {first:'A',second:'V',probability:(blue/n)*(red/(n-(replacement?0:1)))},
    {first:'A',second:'A',probability:(blue/n)*((blue-(replacement?0:1))/(n-(replacement?0:1)))}
  ];},
  draw(red,blue,previous,replacement,rng){let r=red,b=blue;if(previous&&!replacement){if(previous==='red')r--;else b--;}return rng(r+b)<r?'red':'blue';}
});
function probabilityTree(red,blue,replacement){const n=red+blue,k=replacement?0:1;return `<section class="prob-tree"><h3>Árvore das duas retiradas</h3><p>Primeira retirada: <strong>V ${red}/${n}</strong> ou <strong>A ${blue}/${n}</strong>.</p><div class="tree-branches"><div>🔴 V (${red}/${n})<div class="branch">↳ 🔴 V: ${red-k}/${n-k}<br>↳ 🔵 A: ${blue}/${n-k}</div></div><div>🔵 A (${blue}/${n})<div class="branch">↳ 🔴 V: ${red}/${n-k}<br>↳ 🔵 A: ${blue-k}/${n-k}</div></div></div><p><strong>P(VV) = ${red}/${n} × ${red-k}/${n-k} = ${(100*ProbabilityCore.pair(red,blue,replacement)).toFixed(2).replace('.',',')}%</strong></p><small>${replacement?'A gota volta; a composição não muda.':'A gota não volta; a segunda probabilidade depende da primeira.'}</small></section>`;}
