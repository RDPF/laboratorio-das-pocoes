# v0.8.3 — Identificação dos estudantes

## O que mudou

- Ao acessar o link da turma, o estudante recebe uma tela de identificação **antes de começar**: digita um pseudônimo ou número de chamada (por exemplo, `Coruja-17` ou `17`, apresentado como `Nº 17`) ou escolhe **Gerar automaticamente** (`Alquimista-XXXXXX`). Não é necessário nome completo ou cadastro.
- O pseudônimo aparece no cabeçalho durante todas as seis missões. O botão no cabeçalho permite alterá-lo sem perder as tentativas existentes: o identificador técnico permanece igual.
- A identificação é guardada por sala no navegador. Ao reabrir a mesma sala no mesmo navegador, a escolha é recuperada. A primeira turma com dados da v0.8.2 reutiliza o identificador técnico antigo para manter o histórico. Novas turmas têm perfis próprios.
- O servidor registra a identificação **antes da primeira missão** via `POST /api/student-profile`. Se não houver rede, a identificação fica pendente; a fila incorpora a identidade a cada registro e sincroniza quando a conexão retorna.
- Os registros da fila agora carregam a sala **e** o ID técnico do estudante que realizou a missão; uma mudança de turma não atribui dados a outro estudante.
- A aba Avaliação e Diagnóstico exibe pseudônimos e códigos de distinção e pode mostrar inscritos ainda sem tentativas.
- O arquivo HTML único permite personalização local também sem servidor, mas o professor só recebe registros feitos pelo endereço de sua sala e sincronizados com o servidor.

## Como executar

No Miniforge Prompt, dentro da pasta extraída:

```powershell
conda activate labprob
python -m pip install -r servidor/requirements.txt
python iniciar_aula.py --turma 91
```

O professor compartilha o QR Code da aba Descobertas da Turma. No celular o estudante abre o QR Code, escolhe o identificador e joga normalmente. O professor o vê na aba Avaliação e Diagnóstico; a atualização ocorre a cada 15 segundos ou clicando em Atualizar.

## Cuidados

- A identificação é **pseudônima e autodeclarada**; não confirma identidade civil. Se dois estudantes escolherem o mesmo nome, o painel mostra também um código curto para distingui-los.
- O identificador se mantém apenas no mesmo navegador/origem e enquanto os dados locais estiverem presentes. Trocar de navegador, limpar dados ou mudar o endereço IP do servidor pode criar outra identidade.
- Usar um mesmo navegador para estudantes diferentes sem limpar os dados os associará ao mesmo perfil; para uso compartilhado são necessários perfis de navegador separados.
- Registros anteriores sem pseudônimo continuam visíveis com identificador automático; não é possível inferir nomes deles.
- Sala local HTTP não habilita a instalação PWA em IP privado. A conexão turma-servidor requer rede funcional; o jogo individual permanece offline.
- O painel registra apenas resultados e observações; não valida matrícula nem autentica estudantes individualmente.
- Não alteramos a matemática, pontuação ou sequência das seis missões em relação à v0.8.2.
