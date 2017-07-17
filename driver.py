import logging
import time
from racer import Racer

# setup logging
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] (%(threadName)-10s) %(message)s',)
logging.getLogger("requests").setLevel(logging.WARNING)


'''
Driver to run the Racers given a start and an end page.
'''
def drive(start, end, timeout=60, threads=2):
	message = {}

	# data stores shared between threads
	forwardCache = {}
	backCache = {}
	forwardQueue = []
	backVisited = {}
	threading = {
		'waiting': 0,
		'total': threads
	}
	result = {
		'networkTime': 0,
		'isFound': False,
		'path': ''
	}

	# forward racers
	racers = []
	for i in range(threads):
		name = 'start-' + str(i)

		racers.append(Racer(name, 'forward', start, forwardCache, backCache, backVisited, forwardQueue, threading, result))

	# back racer
	racers.append(Racer('end', 'back', end, backCache, forwardCache, backVisited, [], {}, result))

	start = time.time()

	# start and join racers
	for r in racers:
		r.start()

	for r in racers:
		r.join(timeout)

	# complete
	runTime = time.time() - start

	logging.info('Results: ' + str(result))

	# set api response
	message['time'] = runTime

	# check for timeout
	isTimeout = False
	for r in racers:
		if r.isAlive():
			isTimeout = True

	if isTimeout:
		result['isFound'] = True
		message['path'] = 'Timed out.'

	else:
		if 'path' in result:
			message['path'] = result['path']
		
		if 'networkTime' in result:
			message['network'] = result['networkTime'] / 2

	return message