import logging
import sys
import os
import urllib.request
import json
import datetime
import threading
import time
import csv

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
from collections import OrderedDict
from io import StringIO


# Variáveis pré-definidas

CSV_COMMA = ',' # Delimitador do arquivo CSV


class App:
	def __init__(self):
		try:
			self.load()
		except FileNotFoundError:
			print("JSON file with token not found")
			exit(0)

		logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

		self.updater = Updater(token=self.key)
		self.dispatcher = self.updater.dispatcher

		self.dispatcher.add_handler(CommandHandler('start', self.start))
		self.dispatcher.add_handler(CommandHandler('help', self.help))
		self.dispatcher.add_handler(CommandHandler('subscribe', self.subscribe))
		self.dispatcher.add_handler(CommandHandler('unsubscribe', self.unsubscribe))
		self.dispatcher.add_handler(CommandHandler('bcast', self.broadcast))
		self.dispatcher.add_handler(CommandHandler('pin', self.pin))
		self.dispatcher.add_handler(CommandHandler('feedback', self.feedback))
		self.dispatcher.add_handler(CommandHandler('members', self.members))
		self.dispatcher.add_handler(CommandHandler('freq', self.freq))
		self.dispatcher.add_handler(CommandHandler('freqr', self.freqr))
		self.dispatcher.add_handler(CommandHandler('auth', self.authorize))
		self.dispatcher.add_handler(CommandHandler('deauth', self.deAuthorize))
		#self.dispatcher.add_handler(CommandHandler('upcoming', self.upcoming))
		#self.dispatcher.add_handler(CommandHandler('now', self.now))

		self.jobs = self.updater.job_queue
		#self.tick_job = self.jobs.run_repeating(self.tick, interval=self.interval, first=0)

		self.subscribersLock = threading.Lock()

	def load(self):
		with open('config.json', 'r') as f:
			o = json.load(f)
			self.subscribers = set(o['subscribers']) if 'subscribers' in o else set()
			self.authorized = set(o['authorized']) if 'authorized' in o else set()
			self.interval = o['interval'] if 'interval' in o else 300
			self.key = o['key']
			self.membersDriveLink = o['membersDriveLink']
			self.feedbackDriveLink = o['feedbackDriveLink']
			self.frequencyDriveLink = o['frequencyDriveLink']

	def save(self):
		with open('config.json', 'w') as f:
			json.dump({
				'subscribers': list(self.subscribers),
				'authorized': list(self.authorized),
				'interval': self.interval,
				'key': self.key,
				'membersDriveLink': self.membersDriveLink,
				'feedbackDriveLink': self.feedbackDriveLink,
				'frequencyDriveLink': self.frequencyDriveLink,
			}, f, indent=4)

	def run(self):
		self.updater.start_polling()

	def start(self, bot, update):
		msg = "Bem vindo ao Ganesh Bot \\o/\n"
		msg += "Digite /help para uma lista de funcionalidades."
		bot.send_message(chat_id=update.message.chat_id, text=msg)

	def help(self, bot, update):
		msg = "Olá, eu sou o assistente pessoal do Ganesh."
		msg += "\n\nAtualmente tenho esses comandos:\n\n"
		msg += "/start - Começa o bot.\n"
		msg += "/subscribe - Se inscreve para notificações do bot.\n"
		msg += "/unsubscribe - Se desinscreve para notificações do bot.\n"
		msg += "/help - Mostra essa mensagem.\n"

		# Authorized users only:
		message = update.message
		if message.from_user.username in self.authorized:
			msg += "\n__**Admin Only**__\n"
			msg += "/bcast `Mensagem` - Manda a mensagem para todos os usuários inscritos.\n"
			msg += "/pin `Mensagem` - Manda a mensagem para todos os usuários inscritos e fixa (pin) ela nos supergrupos.\n"
			msg += "/members - Mostra estatísticas dos membros do Ganesh.\n"
			msg += "/feedback `Filtro` - Mostra o feedback para a atividade filtrada (o filtro pode ser uma data, por exemplo).\n"
			msg += "/freq `Filtro` - Mostra a frequência nas reuniões para o membro filtrado (o filtro pode ser parte do nome, por exemplo).\n"
			msg += "/freqr `Filtro` - Mostra estatísticas de frequência para a reunião filtrada (o filtro pode ser uma data, por exemplo).\n"
			msg += "/auth `Username` - Autoriza o usuário com @ `Username` a mandar broadcast.\n"
			msg += "/deauth `Username` - Desautoriza o usuário com @ `Username` a mandar broadcast.\n"

		bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True )


	def subscribe(self, bot, update):
		chat_id = update.message.chat_id

		with self.subscribersLock:
			if(chat_id in self.subscribers):
				bot.send_message(chat_id=chat_id, text="Já inscrito!")
				return
			self.subscribers.add(chat_id)
			self.save()
			bot.send_message(chat_id=chat_id, text="Inscrito com sucesso!")

	def unsubscribe(self, bot, update):
		chat_id = update.message.chat_id
		with self.subscribersLock:
			if(chat_id in self.subscribers):
				self.subscribers.remove(chat_id)
				self.save()
				bot.send_message(chat_id=chat_id, text="Desinscrito com sucesso :(")
				return
			bot.send_message(chat_id=chat_id, text="Usuário não inscrito!")

	def authorize(self, bot, update):
		message = update.message
		try: 
			toAuth = message.text.split(' ', 1)[1]
		except:
			bot.send_message(chat_id=message.chat_id, text="Saudades Parâmetros :(")
			return

		username = message.from_user.username
		if username in self.authorized:			
			if(toAuth in self.authorized):
				bot.send_message(chat_id=message.chat_id, text="Já autorizado!")
				return
			self.authorized.add(toAuth)
			self.save()
			bot.send_message(chat_id=message.chat_id, text="Autorizado com sucesso!")
		else:
			bot.send_message(chat_id=message.chat_id, text="Usuário não autorizado :(")

	def deAuthorize(self, bot, update):
		message = update.message
		username = message.from_user.username
		try:
			toDeauth = message.text.split(' ', 1)[1]
		except:
			bot.send_message(chat_id=message.chat_id, text="Saudades Parâmetros :(")
			return

		if username in self.authorized:
			if(toDeauth in self.authorized):
				bot.send_message(chat_id=message.chat_id, text="Usuário removido com sucesso!")
				self.authorized.remove(toDeauth)
				self.save()
			else:
				bot.send_message(chat_id=message.chat_id, text="Usuário não estava na lista!")
		else:
			bot.send_message(chat_id=message.chat_id, text="Usuário não autorizado :(")

	def broadcast(self, bot, update):
		# Gets message text and removes /broadcast command.
		message = update.message
		try:
			sendMsg = message.text.split(' ', 1)[1]
		except:
			bot.send_message(chat_id=message.chat_id, text="Saudades Parâmetros :(")
			return

		if message.from_user.username in self.authorized:
			for subscriber in self.subscribers:
				try:
					bot.send_message(chat_id=subscriber, text=sendMsg, parse_mode=ParseMode.MARKDOWN)
				except Exception as exc:
					print(exc)
					print("Erro ao mandar mensagem. Talvez o chat_id não exista mais/mudou?")
		else:
			bot.send_message(chat_id=message.chat_id, text="Usuário não autorizado :(")

	def pin(self, bot, update):
		# Gets message text and removes /broadcast command.
		message = update.message
		try:
			sendMsg = message.text.split(' ', 1)[1]
		except:
			bot.send_message(chat_id=message.chat_id, text="Saudades Parâmetros :(")
			return

		if message.from_user.username in self.authorized:
			for subscriber in self.subscribers:
				try:
					sentMessage = bot.send_message(chat_id=subscriber, text=sendMsg, parse_mode=ParseMode.MARKDOWN)
					bot.pin_chat_message(chat_id=subscriber, message_id=sentMessage.message_id, disable_notification=False) # Só vai funcionar se o bot for adm do supergrupo.
				except Exception as exc:
					print(exc)
					print("Erro ao mandar mensagem ou pinar ela. Talvez o chat_id não exista mais/mudou? Ou então o bot não enviou para um supergrupo? Ou ele não é adm?")
		else:
			bot.send_message(chat_id=message.chat_id, text="Usuário não autorizado :(")

	def members(self, bot, update): # Calcula o número de membros por curso e ano
		message = update.message
		if not message.from_user.username in self.authorized:
			bot.send_message(chat_id=message.chat_id, text="Usuário não autorizado :(")
			return

		try:
			with StringIO(urllib.request.urlopen(self.membersDriveLink).read().decode('utf-8')) as mStream:
				csvOutput = csv.reader(mStream, delimiter=CSV_COMMA)
				csvLines = list(csvOutput)
		except Exception as exc:
				print(exc)
				bot.send_message(chat_id=message.chat_id, text="Poxa, não consegui baixar a tabela do Drive :(")
				return

		del csvLines[0] # Remove a coluna header
		courses = { }
		nMembers = 0

		for member in csvLines:
			if member[8] == 'Inativo': # Ignorar membros inativos no cálculo
				continue
			nMembers += 1
			if not member[3] in courses:
				courses[member[3]] = [0, {}]
			courses[member[3]][0] += 1
			if member[4] in courses[member[3]][1]:
				courses[member[3]][1][member[4]] += 1
			else:
				courses[member[3]][1][member[4]] = 1

		outputResults = "<strong>== Membros do Ganesh -> " + str(nMembers) + " ==</strong>\n\n"
		for course in sorted(courses):
			outputResults += "<strong>~ " + course + " -> " + str(courses[course][0]) + " (" + str(round(courses[course][0]*100/nMembers, 2)) + "%) ~</strong>\n"
			for year in sorted(courses[course][1]):
				outputResults += "\t" + year + ": " + str(courses[course][1][year]) + " (" + str(round(courses[course][1][year]*100/nMembers, 2)) + "%)\n"
			outputResults += "\n"

		bot.send_message(chat_id=message.chat_id, text=outputResults, parse_mode='HTML')

	def feedback(self, bot, update): # Calcula o feedback das atividades ou reuniões
		message = update.message
		messageList = message.text.split(' ', 1)
		filterFeedback = False
		if len(messageList) > 1:
			queryFilter = messageList[1]
			filterFeedback = True

		if not message.from_user.username in self.authorized:
			bot.send_message(chat_id=message.chat_id, text="Usuário não autorizado :(")
			return

		try:
			with StringIO(urllib.request.urlopen(self.feedbackDriveLink).read().decode('utf-8')) as mStream:
				csvOutput = csv.reader(mStream, delimiter=CSV_COMMA)
				csvLines = list(csvOutput)
		except Exception as exc:
				print(exc)
				bot.send_message(chat_id=message.chat_id, text="Poxa, não consegui baixar a tabela do Drive :(")
				return

		del csvLines[0] # Remove a coluna header
		data = OrderedDict()

		for response in csvLines:
			if not response[1] in data:
				data[response[1]] = [0, {}, {}, {}, [], []]
			data[response[1]][0] += 1
			if response[2] in data[response[1]][1]:
				data[response[1]][1][response[2]] += 1
			else:
				data[response[1]][1][response[2]] = 1
			if response[3] in data[response[1]][2]:
				data[response[1]][2][response[3]] += 1
			else:
				data[response[1]][2][response[3]] = 1
			if response[4] in data[response[1]][3]:
				data[response[1]][3][response[4]] += 1
			else:
				data[response[1]][3][response[4]] = 1
			if response[5]:
				data[response[1]][4].append(response[5])
			if response[6]:
				data[response[1]][5].append(response[6])

		outputResults = [""]
		found = False
		for dataKey in data:
			if filterFeedback and queryFilter not in dataKey:
				continue
			found = True
			feedbackOutput = "<strong>== " + dataKey + ": " + str(data[dataKey][0]) + " feedbacks recebidos ==</strong>\n"
			feedbackOutput += "<em>Gostou do tema da atividade?</em>\n"
			for liked in sorted(data[dataKey][1]):
				feedbackOutput += "\t- " + liked + ": " + str(data[dataKey][1][liked]) + " (" + str(round(data[dataKey][1][liked]*100/data[dataKey][0], 2)) + "%)\n"
			feedbackOutput += "<em>O quanto você entendeu do assunto?</em>\n"
			scoreSum = 0
			for score in sorted(data[dataKey][2]):
				feedbackOutput += "\t- " + score + "/5: " + str(data[dataKey][2][score]) + " (" + str(round(data[dataKey][2][score]*100/data[dataKey][0], 2)) + "%)\n"
				scoreSum += int(score) * data[dataKey][2][score]
			feedbackOutput += "\t- média: " + str(round(scoreSum/data[dataKey][0], 1)) + "/5\n"
			feedbackOutput += "<em>Vale a pena revisar o assunto em reuniões futuras?</em>\n"
			for review in sorted(data[dataKey][3]):
				feedbackOutput += "\t- " + review + ": " + str(data[dataKey][3][review]) + " (" + str(round(data[dataKey][3][review]*100/data[dataKey][0], 2)) + "%)\n"
			feedbackOutput += "<em>Algum assunto que gostaria para próximas atividades ou reuniões?</em>\n"
			if len(data[dataKey][4]) < 1:
				feedbackOutput += "\t(nada)"
			for subject in data[dataKey][4]:
				feedbackOutput += "<pre>" + subject.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") + "</pre>"
			feedbackOutput += "\n<em>Alguma observação ou sugestão de mudança?</em>\n"
			if len(data[dataKey][5]) < 1:
				feedbackOutput += "\t(nada)"
			for suggestion in data[dataKey][5]:
				feedbackOutput += "<pre>" + suggestion.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") + "</pre>"
			feedbackOutput += "\n\n"
			if len(outputResults[len(outputResults) - 1]) + len(feedbackOutput) > 4050:
				outputResults.append(feedbackOutput)
			else:
				outputResults[len(outputResults) - 1] += feedbackOutput

		if found:
			for string in outputResults: # Envia as mensagens separadamente pq não pode estrapolar o limite de 4096 caracteres
				bot.send_message(chat_id=message.chat_id, text=string, parse_mode='HTML', disable_web_page_preview=True)
		elif filterFeedback:
			bot.send_message(chat_id=message.chat_id, text="Nada encontrado com <strong>" + queryFilter.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") + "</strong> :(", parse_mode='HTML', disable_web_page_preview=True)
		else:
			bot.send_message(chat_id=message.chat_id, text="Nada encontrado :(")

	def freq(self, bot, update): # Calcula a frequência dos membros
		message = update.message
		messageList = message.text.split(' ', 1)
		filterFrequency = False
		if len(messageList) > 1:
			queryFilter = messageList[1]
			filterFrequency = True

		if not message.from_user.username in self.authorized:
			bot.send_message(chat_id=message.chat_id, text="Usuário não autorizado :(")
			return

		try:
			with StringIO(urllib.request.urlopen(self.frequencyDriveLink).read().decode('utf-8')) as mStream:
				csvOutput = csv.reader(mStream, delimiter=CSV_COMMA)
				csvLines = list(csvOutput)
		except Exception as exc:
				print(exc)
				bot.send_message(chat_id=message.chat_id, text="Poxa, não consegui baixar a tabela do Drive :(")
				return

		members = { }

		for member in csvLines[2:]:
			members[member[1]] = [int(member[2]), int(member[4]), int(member[5]), member[8:]]

		outputResults = [""]
		found = False
		for member in sorted(members):
			if filterFrequency and queryFilter not in member:
				continue
			if not found:
				outputResults[0] += "<strong>[NOME]: [N_PRESENÇAS] [N_JUSTIFICATIVAS] [N_FALTAS] ([%PRESENTE] [%JUSTIFICADO]) ->"
				for date in csvLines[0][8:]:
					outputResults[0] += " [" + date + "]"
				outputResults[0] += "</strong>\n\n"
			found = True
			userOutput = member + ": " + str(members[member][0]) + " " + str(members[member][1]) + " " + str(members[member][2]) + " ("
			userOutput += str(round(members[member][0] * 100 / (members[member][0] + members[member][1] + members[member][2]), 2)) + "% "
			userOutput += str(round((members[member][0] + members[member][1]) * 100 / (members[member][0] + members[member][1] + members[member][2]), 2)) + "%) ->"
			for freq in members[member][3]:
				userOutput += " " + freq
			userOutput += "\n"
			if len(outputResults[len(outputResults) - 1]) + len(userOutput) > 4050:
				outputResults.append(userOutput)
			else:
				outputResults[len(outputResults) - 1] += userOutput
			

		if found:
			for string in outputResults: # Envia as mensagens separadamente pq não pode estrapolar o limite de 4096 caracteres
				bot.send_message(chat_id=message.chat_id, text=string, parse_mode='HTML')
		elif filterFrequency:
			bot.send_message(chat_id=message.chat_id, text="Nada encontrado com <strong>" + queryFilter.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") + "</strong> :(", parse_mode='HTML', disable_web_page_preview=True)
		else:
			bot.send_message(chat_id=message.chat_id, text="Nada encontrado :(")

	def freqr(self, bot, update): # Calcula a frequência das reuniões
		message = update.message
		messageList = message.text.split(' ', 1)
		filterFrequency = False
		if len(messageList) > 1:
			queryFilter = messageList[1]
			filterFrequency = True

		if not message.from_user.username in self.authorized:
			bot.send_message(chat_id=message.chat_id, text="Usuário não autorizado :(")
			return

		try:
			with StringIO(urllib.request.urlopen(self.frequencyDriveLink).read().decode('utf-8')) as mStream:
				csvOutput = csv.reader(mStream, delimiter=CSV_COMMA)
				csvLines = list(csvOutput)
		except Exception as exc:
				print(exc)
				bot.send_message(chat_id=message.chat_id, text="Poxa, não consegui baixar a tabela do Drive :(")
				return

		data = OrderedDict()

		for member in csvLines[2:]:
			for dateKey in range(8, len(csvLines[0])):
				if not csvLines[0][dateKey] in data:
					data[csvLines[0][dateKey]] = [[], [], []]
				if member[dateKey] == 'P':
					data[csvLines[0][dateKey]][0].append(member[1])
				elif member[dateKey] == 'J':
					data[csvLines[0][dateKey]][1].append(member[1])
				else:
					data[csvLines[0][dateKey]][2].append(member[1])

		outputResults = [""]
		found = False
		for date in data:
			if filterFrequency and queryFilter not in date:
				continue
			if not found:
				outputResults[0] += "<strong>== Total de membros: " + str(len(data[date][0]) + len(data[date][1]) + len(data[date][2])) + " ==</strong>\n\n"
			found = True
			frequencyOutput = "<strong>== " + date + " ==</strong>\n"
			frequencyOutput += "\tPresenças: " + str(len(data[date][0])) + " (" + str(round(len(data[date][0])*100/(len(data[date][0]) + len(data[date][1]) + len(data[date][2])), 2)) + "%)\n"
			frequencyOutput += "\tJustificativas: " + str(len(data[date][1])) + " (" + str(round(len(data[date][1])*100/(len(data[date][0]) + len(data[date][1]) + len(data[date][2])), 2)) + "%)\n"
			frequencyOutput += "\tPresenças contabilizadas: " + str(len(data[date][0]) + len(data[date][1])) + " (" + str(round((len(data[date][0]) + len(data[date][1]))*100/(len(data[date][0]) + len(data[date][1]) + len(data[date][2])), 2)) + "%)\n"
			frequencyOutput += "\tFaltas: " + str(len(data[date][2])) + " (" + str(round(len(data[date][2])*100/(len(data[date][0]) + len(data[date][1]) + len(data[date][2])), 2)) + "%)\n"
			frequencyOutput += "\tPresentes:\n<pre>"
			frequencyOutput += sorted(data[date][0])[0]
			for member in sorted(data[date][0])[1:]:
				frequencyOutput += ", " + member
			frequencyOutput += "</pre>\n\tJustificaram:\n<pre>"
			frequencyOutput += sorted(data[date][1])[0]
			for member in sorted(data[date][1])[1:]:
				frequencyOutput += ", " + member
			frequencyOutput += "</pre>\n\n"
			if len(outputResults[len(outputResults) - 1]) + len(frequencyOutput) > 4050:
				outputResults.append(frequencyOutput)
			else:
				outputResults[len(outputResults) - 1] += frequencyOutput
			

		if found:
			for string in outputResults: # Envia as mensagens separadamente pq não pode estrapolar o limite de 4096 caracteres
				bot.send_message(chat_id=message.chat_id, text=string, parse_mode='HTML')
		elif filterFrequency:
			bot.send_message(chat_id=message.chat_id, text="Nada encontrado com <strong>" + queryFilter.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") + "</strong> :(", parse_mode='HTML', disable_web_page_preview=True)
		else:
			bot.send_message(chat_id=message.chat_id, text="Nada encontrado :(")

	# CTF Functionalities, to be done in the future.

	# def tick(self, bot, job):
	# 	oneDay = int(time.time()) + 86400 #1 day
	# 	oneHour = int(time.time()) + 3600 #1 hour

	# 	fmtstr = '%Y-%m-%dT%H:%M:%S'

	# 	fDay = urllib.request.urlopen('https://ctftime.org/api/v1/events/?limit=1&start={}'.format(oneDay-300))
	# 	lDay = json.load(fDay)
	# 	for oDay in lDay:
	# 		oDay['start'] = datetime.datetime.strptime(oDay['start'][:-6], fmtstr)

	# 	fHour = urllib.request.urlopen('https://ctftime.org/api/v1/events/?limit=1&start={}'.format(oneHour-300))
	# 	lHour = json.load(fHour)
	# 	for oHour in lHour:
	# 		oHour['start'] = datetime.datetime.strptime(oHour['start'][:-6], fmtstr)

	# 	#print(int(o['start'].timestamp())) # starting event time
	# 	with self.subscribersLock:
	# 		for subscriber in self.subscribers:
	# 			if(int(oDay['start'].timestamp()) < oneDay):
	# 				msg = "[" + oDay['title'] + "](" + oDay['url'] + ") will start in 1 day."
	# 				bot.send_message(chat_id=subscriber, text=msg, parse_mode=ParseMode.MARKDOWN)
	# 			if(int(oHour['start'].timestamp()) < oneHour):
	# 				msg = '[' + oHour['title'] + '](' + oHour['url'] + ") will start in 1 hour."
	# 				bot.send_message(chat_id=subscriber, text=msg, parse_mode=ParseMode.MARKDOWN)

	# def list_events(self):
	# 	fmtstr = '%Y-%m-%dT%H:%M:%S'
	# 	now = int(time.time())
	# 	nextweek = now + 604800 * 4 # printing time in weeks

	# 	f = urllib.request.urlopen('https://ctftime.org/api/v1/events/?limit=5&start={}&finish={}'.format(now, nextweek))
	# 	l = json.load(f)
	# 	newL = []
	# 	genstr = '%a, %B %d, %Y %H:%M UTC '	#

	# 	for o in l:
	# 		o['start'] = datetime.datetime.strptime(o['start'][:-6], fmtstr)
	# 		o['start'] = o['start'].strftime(genstr)
	# 		newL.append(o)

	# 	return newL


	# def upcoming(self, bot, update):
	# 	l = self.list_events()
	# 	msg = "*Upcoming Events:*"
	# 	for o in l:
	# 		msg += '\n' + '[' + o['title'] + ']' + '(' + o['url'] + ') ' + '\n'
	# 		msg += o['format'] + '\n'
	# 		msg += str(o['start']) + '\n'
	# 		if(o['duration']['days'] > 1):
	# 			msg += 'Duration: ' + str(o['duration']['days']) + ' days'
	# 			if(o['duration']['hours']):
	# 				msg += ' and ' + str(o['duration']['hours']) + ' hours\n'
	# 			else:
	# 				msg += '\n'
	# 		elif(o['duration']['days'] == 1):
	# 			msg += 'Duration: ' + str(o['duration']['days']) + ' day'
	# 			if(o['duration']['hours']):
	# 				msg += ' and ' + str(o['duration']['hours']) + ' hours\n'
	# 			else:
	# 				msg += '\n'
	# 		else: #0 days
	# 			if(o['duration']['hours']):
	# 				msg += 'Duration: ' + str(o['duration']['hours']) + ' hours\n'

	# 	bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)


	# def list_happening(self):
	# 	fmtstr = '%Y-%m-%dT%H:%M:%S'
	# 	now = int(time.time())
	# 	daysAgo = now - 300000

	# 	f = urllib.request.urlopen('https://ctftime.org/api/v1/events/?limit=5&start={}'.format(daysAgo))
	# 	l = json.load(f)
	# 	newL = []
	# 	genstr = '%a, %B %d, %Y %H:%M UTC '	#

	# 	for o in l:			
	# 		o['start'] = datetime.datetime.strptime(o['start'][:-6], fmtstr)	
	# 		o['finish'] = datetime.datetime.strptime(o['finish'][:-6], fmtstr)	
	# 		if(int(o['start'].timestamp()) > daysAgo):
	# 			if(int(o['finish'].timestamp()) > now):
	# 				o['start'] = o['start'].strftime(genstr)
	# 				newL.append(o)

	# 	return newL

	# def now(self, bot, update):
	# 	l = self.list_happening()
	# 	msg = "*Events Happening Now:*"
	# 	for o in l:
	# 		msg += '\n' + '[' + o['title'] + ']' + '(' + o['url'] + ') ' + '\n'
	# 		msg += o['format'] + '\n'
	# 		msg += 'Started: ' + str(o['start']) + '\n'
	# 		if(o['duration']['days'] > 1):
	# 			msg += 'Duration: ' + str(o['duration']['days']) + ' days'
	# 			if(o['duration']['hours']):
	# 				msg += ' and ' + str(o['duration']['hours']) + ' hours\n'
	# 			else:
	# 				msg += '\n'
	# 		elif(o['duration']['days'] == 1):
	# 			msg += 'Duration: ' + str(o['duration']['days']) + ' day'
	# 			if(o['duration']['hours']):
	# 				msg += ' and ' + str(o['duration']['hours']) + ' hours\n'
	# 			else:
	# 				msg += '\n'
	# 		else: #0 days
	# 			if(o['duration']['hours']):
	# 				msg += 'Duration: ' + str(o['duration']['hours']) + ' hours\n'

	# 	bot.send_message(chat_id=update.message.chat_id, text=msg, parse_mode=ParseMode.MARKDOWN)


if __name__ == '__main__':
	App().run()
