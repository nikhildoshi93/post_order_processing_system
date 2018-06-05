# Scalable order post processing system
    Design a system to send sms, mail and invoice after order is placed.
    The individual components should run as independent microservice to make it scalable. 
    If invoice is generated successfully, order mail should have invoice attached, 
    otherwise a footer message "We will send invoice soon" should be present. 
    And then you send invoice later when it gets generated.

# Includes:

- Mail service
- Invoice service
- Order info service
