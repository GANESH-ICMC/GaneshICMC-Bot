import logging
import sys
import os
import urllib.request
import json
import datetime
import threading
import time

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode


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

	def save(self):
		with open('config.json', 'w') as f:
			json.dump({
				'subscribers': list(self.subscribers),
				'authorized': list(self.authorized),
				'interval': self.interval,
				'key': self.key,
			}, f, indent=4)

	def run(self):
		self.updater.start_polling()

	def start(self, bot, update):
		msg = "Bem vindo ao Ganesh Bot \o/\n"
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
		authUser = 0
		message = update.message

		username = message.from_user.username
		for username in self.authorized:
			authUser = 1

		if authUser == 1:
			msg += "\n__**Admin Only**__\n"
			msg += "/bcast `Mensagem` - Manda a mensagem para todos os usuários inscritos.\n"
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
		authUser = 0
		message = update.message
		try: 
			toAuth = message.text.split(' ', 1)[1]
		except:
			bot.send_message(chat_id=message.chat_id, text="Saudades Parâmetros :(")
			return

		username = message.from_user.username
		for auth in self.authorized:
			if username == auth:
				authUser = 1

		if authUser == 0:			
			bot.send_message(chat_id=message.chat_id, text="Usuário não autorizado :(")
		else:
			if(toAuth in self.authorized):
				bot.send_message(chat_id=message.chat_id, text="Já autorizado!")
				return
			self.authorized.add(toAuth)
			self.save()
			bot.send_message(chat_id=message.chat_id, text="Autorizado com sucesso!")

	def deAuthorize(self, bot, update):
		message = update.message
		username = message.from_user.username
		#print (message)
		authUser = 0
		try:
			toDeauth = message.text.split(' ', 1)[1]
		except:
			bot.send_message(chat_id=message.chat_id, text="Saudades Parâmetros :(")
			return

		for auth in self.authorized:
			if username == auth:
				authUser = 1

		if authUser == 0:			
			bot.send_message(chat_id=message.chat_id, text="Usuário não autorizado :(")
		else:
			if(toDeauth in self.authorized):
				bot.send_message(chat_id=message.chat_id, text="Usuário removido com sucesso!")
				self.authorized.remove(toDeauth)
				self.save()
			else:
				bot.send_message(chat_id=message.chat_id, text="Usuário não estava na lista!")

	def broadcast(self, bot, update):
		# Gets message text and removes /broadcast command.
		message = update.message
		print(message)
		try:
			sendMsg = message.text.split(' ', 1)[1]
		except:
			bot.send_message(chat_id=message.chat_id, text="Saudades Parâmetros :(")
			return
		authSend = 0
		print(message)

		if message.from_user.username in self.authorized:
			authSend = 1

		if authSend == 0:
			bot.send_message(chat_id=message.chat_id, text="Usuário não autorizado :(")
		else:
			for subscriber in self.subscribers:
				bot.send_message(chat_id=subscriber, text=sendMsg, parse_mode=ParseMode.MARKDOWN)


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
