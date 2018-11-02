# GaneshICMC-Bot
Este robô para Telegram possibilita que os membros e a coordenadoria do Ganesh mantenham algumas de suas atividades e cronograma melhor organizados.

## config.json
Para pleno funcionamento, é necessário construir um arquivo config.json com a seguinte estrutura: <br>
{ <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;	- "subscribers": lista de canais que recebem os broadcasts; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;	- "authorized": lista de usuários do Telegram administradores; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;	- "interval": ?; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;	- "key": chave da Telegram API; <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;	- "membersDriveLink": link do Google Drive para download da tabela CSV dos membros do Ganesh (formato: https://docs.google.com/spreadsheet/ccc?output=csv&key=FORM-KEY]); <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;	- "feedbackDriveLink": link do Google Drive para download da tabela CSV dos Feedbacks recebidos (formato: https://docs.google.com/spreadsheet/ccc?output=csv&key=FORM-KEY]); <br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;	- "frequencyDriveLink": link do Google Drive para download da tabela CSV das frequências dos membros (formato: https://docs.google.com/spreadsheet/ccc?output=csv&key=FORM-KEY]). <br>
}
