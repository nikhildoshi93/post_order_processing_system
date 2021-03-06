'''
Author - Nikhil

Order info service:
	- Order information persistence layer
	- REST APIs exposed to provide order info as a resource

'''

## Library imports
import json

## Library imports
from django.db import transaction
from models import order_info, notification_request


def notification_status_GET_(request):
	'''
	GET API
		request contains the order_id
		Response codes: 200, 300, 404, 501
		Response data: Notification status for the order_id
	'''

	# Parsing the request
	notification_request = json.load(request.data)
	
	# Notification status contains corresponding order_id
	order_id = notification_request['order_id']

	# Fetch the order and notification status objects
	order_info_obj = order_info.objects.get(order_id = order_id)

	notification_id = order_info_obj.notification_id
	notification_obj = notification_status.get(notification_id = notification_id)

	# Parse the notification object for status and create json packet
	status = notification_obj.status

	json_packet = json.dump(status)

	# Return the json_packet with response code to be handled by the web service
	return json_packet, 200


def notification_status_POST_(request):
	'''
	POST API
		request contains the complete notification status info
		Response codes: 200, 300, 404, 501
	'''

	# Parsing the request
	status_request = json.load(request.data)

	order_id = status_request['order_id']
	status = status_request['status']

	# Fetching the relevant order and notification status objects
	order_info_obj = order_info.objects.get(order_id = order_id)

	notification_id = order_info_obj.notification_id
	notification_obj = notification_status.get(notification_id = notification_id)

	# Update the notification status
	notification_obj.status = status

	# Atomic db call
	with transaction.atomic():

		# Probably can get the object in the transaction as well if required
		notification_obj.save()


def update_mail_status_POST_(request):
	'''
	POST API
		request to update mail_status
		Repsonse codes: 200, 300, 501
	'''

	# For simplicity's sake, making two calls from this API call
	# 1. Get notification status packet, update the relevant information
	# 2. Post the notification status packet

	# Parse the order_id and status request
	request_info = json.load(request.data)

	order_id = request_info['order_id']
	mail_status = request_info['status']

	# Get the notification status packet
	# Maybe create a new request with just the order id
	response = notification_status_GET_(request)

	# Parse the notification response
	notification_info = json.load(response.data)
	status = notification_info['status']

	# Update the mail_status
	status['mail_status'] = mail_status

	# Create new request to post
	request = make_request(order_id, status) # To create a request object

	# Post the notification status
	notification_status_POST_(request)


# A bit of code duplication, can pluck out common code as functions
def update_invoice_status_POST_(request):
	'''
	POST API
		request to update invoice_status
		Repsonse codes: 200, 300, 501
	'''

	# For simplicity's sake, making two calls from this API call
	# 1. Get notification status packet, update the relevant information
	# 2. Post the notification status packet

	# Parse the order_id and status request
	request_info = json.load(request.data)

	order_id = request_info['order_id']
	invoice_status = request_info['status']

	# Get the notification status packet
	# Maybe create a new request with just the order id
	response = notification_status_GET_(request)

	# Parse the notification response
	notification_info = json.load(response.data)
	status = notification_info['status']

	# Update the mail_status
	status['invoice_status'] = invoice_status

	# Create new request to post
	request = make_request(order_id, status) # To create a request object

	# Post the notification status
	notification_status_POST_(request)
