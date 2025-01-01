# ChefBot <br>

An interactive chatbot for food ordering platform for small scale restaurents/eateries. <br>

Project prerequisits:- <br>
-> verified account on Google Dialogflow <br>
->verified account on Ngrok <br>
-> pip installations : pip install fastapi, pip install uvicorn(pip install uvicorn wheel, alternatively), pip install mysql.connector <br>

Steps to build:- <br>
-> download the ngrok.exe file from https://download.ngrok.com/windows?tab=download for Windows 64 bit <br>
-> place the file in the 'chatbot' folder <br>
-> run the FastAPI server in the 'chatbot' directory using the command uvicorn main:app --reload <br>
-> run the ngrok command in the same directory to generate the https URL corresponding to the localhost server http URL <br>
-> ngrok command : ngrok http 8000 <br>
-> paste the ngrok url generated in thee Dialogflow chatbot, under the 'Fulfillments' section by enabling the webhook permission <br>
