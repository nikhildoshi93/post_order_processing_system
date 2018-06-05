'''
Author - Nikhil

Mail service: 
	- Message queue to receive mail requests
	- Workers to consume from the queue
	- API endpoint exposed to receive mail request and API calls to order_info_service and mailer

'''

## Library imports
import json
import requests
from multiprocessing import Process, Queue, cpu_count

## Module imports
from .config import get_config


# Extracting the service endpoints from config
# Meant to be pulled from or managed by API gateway
order_info_service = get_config('order_info_service_endpoint') # Endpoint to update mail notification status
mailer = get_config('mailer_endpoint')

# Message Queue using the process and thread-safe Queue() impl
message_queue = Queue()

# Producer mimick
producer_mock = Process(target = producer, args = (message_queue,))

# Consumers equal to the CPU count
cores_available = cpu_count()

# Create workers
workers = []
for n in range(cores_available):
	# Create consumer process
	c = Process(target = consumer, args = (message_queue, order_info_service, mailer))
	workers.append(c)

## Producer thread spawn
producer_mock.start()

## Worker threads spawned. Can implement thread pool to manage life cycle
for worker in workers:
	worker.start()


############################################
# Producer Logic + REST APIs
############################################


def producer(message_queue):
	'''
	Mimicks the notification service, pushes mail requests
	'''

	def mail_notification_request_POST_(request):
		'''
		POST API
			request contains mail notification related content
			Response codes: 200, 501
		'''

		# Extract and parse request information
		request_info = request.data

		# Push request to message queue
		message_queue.put(request_info.data)

		# Successful response code returned to the web service
		return 200


############################################
# Consumer Logic
############################################


def consumer(message_queue, order_info_service, mailer):
	'''
	Workers pick up requests from the queue and process them one after other.
	To make things simpler, invoice is always sent along with order information, 
	hence the second mail along with invoice looks like the original mail if the
	invoice had been successfully generated.
	'''

	# Extract request from queue
	mail_request = message_queue.get()

	# If poison pill found, push it back and end the consumer
	if mail_request is None:
		message_queue.put(None)

	# Parse and Process mail request
	mail_info = json.load(mail_request)

	email = mail_info['user_mail_id']
	order_info = mail_info['order_info']

	# Fetch invoice status from order_info_service
	invoice_response = requests.get(order_info_service)
	invoice_data = json.load(invoice_response.data)
	
	# Case where the invoice has been successfully generated
	if invoice_data['status']:
		invoice_info = invoice_data['invoice_info']
		
		# Mail status to be pushed to order_info_service
		mail_status = 'invoice_pending'

	# Case when the invoice hasn't been generated, a string 
	# is attached promising invoice delivery later on.
	else:
		invoice_info = 'We will send invoice soon'

		# Mail status to be pushed to order_info_service
		mail_status = 'finished'

	# Generating json packet to send to the mailer
	json_packet = json.dump({       \
		'email' : email,            \
		'order_info' : order_info,  \
		'invoice' : invoice_info
	})

	# To be handled by API gateway
	# Assuming that the mailer can parse all the relevant details and create an email
	mailer_response = requests.post(mailer, data = json_packet)

	# Parse the response sent by the mailer
	if mailer_response.response_code == 200:

		# Creating json packet to update order notification status
		order_id = order_info['order_id']

		json_packet = json.dump({         \
			'order_id' : order_id,        \
			'mail_status' : mail_status
		})

		# Update order info service regarding successful mail
		request.post(order_info_service, data = json_packet)

	# Handle unsuccessful attempts
	else:
		
		# Pushing back to the queue to re-process it again
		message_queue.put(mail_request)


	# Loop-back the consumer to continue with the next request/packet
	consumer(message_queue)


