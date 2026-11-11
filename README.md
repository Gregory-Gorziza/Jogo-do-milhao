# Jogo do Milhão

Aplicação web de perguntas e respostas feita com Flask. O banco fica em
`questions.py`, em matrizes paralelas com 10 níveis e 50 posições por nível.
Cada posição junta uma pergunta, uma resposta certa, três respostas erradas
e uma dica opcional. Todos os 10 níveis têm 50 perguntas cadastradas.

## Onde cadastrar perguntas

As perguntas fornecidas ocupam as 50 posições de cada nível. Se adicionar
perguntas futuramente, use a mesma posição nos arrays
`PERGUNTAS`, `RESPOSTAS_CERTAS`, `RESPOSTAS_ERRADAS_1`,
`RESPOSTAS_ERRADAS_2` e `RESPOSTAS_ERRADAS_3`. A dica é opcional e fica
em `DICAS`, nessa mesma posição. Os índices começam em zero: `[0][0]` é
nível 1, pergunta 1; `[0][1]` é nível 1, pergunta 2; `[1][0]` é nível 2,
pergunta 1.

Cadastre uma questão preenchendo os arrays correspondentes:

```python
PERGUNTAS[0][0] = "Qual é a capital do Brasil?"
RESPOSTAS_CERTAS[0][0] = "Brasília"
RESPOSTAS_ERRADAS_1[0][0] = "Salvador"
RESPOSTAS_ERRADAS_2[0][0] = "Recife"
RESPOSTAS_ERRADAS_3[0][0] = "Manaus"
DICAS[0][0] = "A capital foi inaugurada em 1960."
```

Repita para cada pergunta, mudando os índices. A posição `[nivel][linha]`
é o identificador da questão: todos os textos da questão precisam estar
nessa mesma posição. Deixe as posições ainda não cadastradas como `None`.
O jogo sorteia entre as perguntas preenchidas e informa se o nível atual
ainda não tem perguntas.

As três respostas erradas e a certa devem ser textos diferentes. O jogo
embaralha as quatro alternativas sempre que uma nova pergunta é sorteada,
inclusive ao iniciar uma nova partida. A ordem fica salva na sessão: apenas
recarregar a página não muda as alternativas da pergunta atual.

## Executar

No Windows, execute `iniciar.bat` com duplo clique. Na primeira vez, ele cria
o ambiente virtual e instala as dependências; depois, inicia o jogo. Abra
`http://127.0.0.1:5000` no navegador.

Para iniciar manualmente:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:FLASK_SECRET_KEY = "use-uma-chave-aleatoria"
python app.py
```

Abra `http://127.0.0.1:5000` no navegador. Para desenvolvimento com recarga
automática, defina também `$env:FLASK_DEBUG = "1"` antes de iniciar.

## Regras incluídas

- A pergunta sorteada permanece a mesma ao atualizar a página.
- Resposta incorreta encerra a partida; resposta correta avança um nível.
- O jogador pode parar e levar o valor já garantido.
- Há três pulos por partida e uma utilização de cada uma das ajudas Metade e
  Dica por partida.
- A ajuda Metade esconde duas respostas erradas, e a Dica mostra uma pista.
- A sessão mantém o nível, a pergunta, o prêmio e os usos das ajudas.
- A ordem embaralhada das alternativas também fica na sessão para que
  atualizar a página não altere a resposta correta exibida.

Em produção, defina `FLASK_SECRET_KEY` como uma chave aleatória e mantenha
`FLASK_DEBUG` desativado.
