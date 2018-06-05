'''
Author - Nikhil

Invoice service:
	- Message queue to receive mail requests
	- Workers to consume from the queue 
	- API endpoint exposed to receive invoice generation requests and API calls made to both mail_service and order_info_service

'''

## Library imports
import json
import requests
from multiprocessing import Process, Queue, cpu_count

## Module imports
from .config import get_config

# Extracting the service endpoints from config
# Meant to be pulled from or managed by API gateway
notification_status_endpoint = get_config('notification_status_endpoint')
order_info_service = get_config('order_info_service_endpoint')

## Message Queue using the process and thread-safe Queue() impl
message_queue = Queue()

## Producer mimick
producer_mock = Process(target = producer, args = (message_queue,))

## Consumers equal to the CPU count
cores_available = cpu_count()

## Create workers
workers = []
for n in range(cores_available):
	# Create consumer process
	c = Process(target = consumer, args = (message_queue, notification_status_endpoint, mail_service))
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
	Mimicks the notification service, pushes invoice generation requests
	'''

	def invoice_generation_request_POST_():
		'''
		POST API
			request contains invoice generation request and relevant information
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


def consumer(message_queue, notification_status_endpoint, mail_service):
	'''
	Workers pick up requests from the queue and process them one after other.
	If invoice is generated after the mail service sent the mail, a new mail request is 
	pushed to the mail service. Updates the notification status using the order info service.
	'''

	# Extract request from queue
	invoice_request = message_queue.get()

	# If poison pill found, push it back and end the consumer
	if invoice_request is None:
		message_queue.put(None)

	# Process mail request
	invoice_info = json.load(invoice_request)

	# Generate the invoice, stub function
	invoice = invoice_generator(invoice_info)
	invoice_uri = push_invoice_to_data_store(invoice)

	# Create json_packet and enquire if the mail has been sent
	json_packet = json.load({ order_id : invoice_info['order_id'] })
	status_request = requests.get(notification_status_endpoint, data = json_packet)
	status_info = json.load(status_request)

	# If mail has been sent push a new mail request to the mail_service
	if status_info['mail_status'] == 'invoice_pending':

		# Create json packet and POST it to mail_service, stub function
		json_packet = create_mail_request_packet(invoice_info['order_id'])
		requests.post(mail_service, data = json_packet)

	# Update the notification status

	json_packet = json.dump({             \
		'order_id' : order_id,            \
		'invoice_status' : 'finished'     \
		'invoice_uri' : invoice_uri
	})


	# Loop-back the consumer to continue with the next request/packet
	consumer(message_queue)


