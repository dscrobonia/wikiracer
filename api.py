import web
import json
import driver

urls = (
	'/race', 'race'
)

class race:

	def GET(self):
		message = {}

		data = web.input()

		if 'start' not in data or str(data.start.encode('utf-8')) is '':
			self.addError(message, 'please specify a start page')

		if 'end' not in data or str(data.end.encode('utf-8')) is '':
			self.addError(message, 'please specify a end page')

		if 'start' in data and 'end' in data:
			timeout = 60
			threads = 1

			# read in timeout if specified
			if 'timeout' in data:
				try:
					if int(data.timeout) > 0 and int(data.timeout) < 1000:
						timeout = int(data.timeout)

					else:
						self.addError(message, 'invalid timeout - please specify a timeout between 1 and 999')

				except ValueError as e:
					self.addError(message, 'invalid timeout - timeout could not be read as int')

			# read in threads if specified
			if 'threads' in data:
				try:
					if int(data.threads) > 0 and int(data.threads) < 10:
						threads = int(data.threads)

					else:
						self.addError(message, 'invalid thread count - please specify a thread count between 1 and 9')

				except ValueError as e:
					self.addError(message, 'invalid thread count - thread count could not be read as int')

			# run the racers
			if 'errors' not in message:
				result = driver.drive(data.start, data.end, timeout, threads)

				if 'error' in result:
					self.addError(message, result['error'])

				elif 'path' in result:
					message['result'] = result['path']
					message['time'] = result['time']

		return json.dumps(message)

	def addError(self, message, text):
		if 'errors' not in message:
			message['errors'] = []
		message['errors'].append(text)

if __name__ == "__main__":
	app = web.application(urls, globals())
	app.run()