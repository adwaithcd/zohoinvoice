""" This file contains all functions corresponding to their urls"""

import json
import urllib
import uuid
import traceback

import requests
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from yellowant import YellowAnt
from yellowant.messageformat import MessageClass, MessageAttachmentsClass, \
    MessageButtonsClass, AttachmentFieldsClass

from .commandcentre import CommandCentre
from .models import YellowUserToken, YellowAntRedirectState, \
    AppRedirectState, ZohoInvoiceUserToken

SCOPES = ['ZohoInvoice.contacts.Create',
          'ZohoInvoice.contacts.UPDATE',
          'ZohoInvoice.contacts.READ',
          'ZohoInvoice.contacts.DELETE',
          'ZohoInvoice.settings.Create',
          'ZohoInvoice.settings.UPDATE',
          'ZohoInvoice.settings.READ',
          'ZohoInvoice.settings.DELETE',
          'ZohoInvoice.estimates.Create',
          'ZohoInvoice.estimates.UPDATE',
          'ZohoInvoice.estimates.READ',
          'ZohoInvoice.estimates.DELETE',
          'ZohoInvoice.invoices.Create',
          'ZohoInvoice.invoices.UPDATE',
          'ZohoInvoice.invoices.READ',
          'ZohoInvoice.invoices.DELETE',
          'ZohoInvoice.customerpayments.Create',
          'ZohoInvoice.customerpayments.UPDATE',
          'ZohoInvoice.customerpayments.READ',
          'ZohoInvoice.customerpayments.DELETE',
          'ZohoInvoice.creditnotes.Create',
          'ZohoInvoice.creditnotes.UPDATE',
          'ZohoInvoice.creditnotes.READ',
          'ZohoInvoice.creditnotes.DELETE',
          'ZohoInvoice.projects.Create',
          'ZohoInvoice.projects.UPDATE',
          'ZohoInvoice.projects.READ',
          'ZohoInvoice.projects.DELETE',
          'ZohoInvoice.expenses.Create',
          'ZohoInvoice.expenses.UPDATE',
          'ZohoInvoice.expenses.READ',
          'ZohoInvoice.expenses.DELETE'
         ]


def redirectToYellowAntAuthenticationPage(request):
    """Initiate the creation of a new user integration on YA
       YA uses oauth2 as its authorization framework.
       This method requests for an oauth2 code from YA to start creating a
       new user integration for this application on YA.
    """
    # Generate a unique ID to identify the user when YA returns an oauth2 code
    user = User.objects.get(id=request.user.id)
    state = str(uuid.uuid4())

    # Save the relation between user and state so that we can identify the user
    # when YA returns the oauth2 code
    YellowAntRedirectState.objects.create(user=user.id, state=state)

    # Redirect the application user to the YA authentication page.
    # Note that we are passing state, this app's client id,
    # oauth response type as code, and the url to return the oauth2 code at.
    return HttpResponseRedirect("{}?state={}&client_id={}&response_type=code&redirect_url={}".format
                                (settings.YELLOWANT_OAUTH_URL, state, settings.YELLOWANT_CLIENT_ID,
                                 settings.YELLOWANT_REDIRECT_URL))


def yellowantRedirecturl(request):
    """ Receive the oauth2 code from YA to generate a new user integration
            This method calls utilizes the YA Python SDK to create a new user integration on YA.
            This method only provides the code for creating a new user integration on YA.
            Beyond that, you might need to authenticate the user on
            the actual application (whose APIs this application will be calling)
            and store a relation between these user auth details and the YA user integration.
    """
    # Oauth2 code from YA, passed as GET params in the url
    code = request.GET.get('code')

    # The unique string to identify the user for which we will create an integration
    state = request.GET.get("state")

    # Fetch user with help of state from database
    yellowant_redirect_state = YellowAntRedirectState.objects.get(state=state)
    user = yellowant_redirect_state.user

    # Initialize the YA SDK client with your application credentials
    y = YellowAnt(app_key=settings.YELLOWANT_CLIENT_ID,
                  app_secret=settings.YELLOWANT_CLIENT_SECRET, access_token=None,
                  redirect_uri=settings.YELLOWANT_REDIRECT_URL)

    # Getting the acccess token
    access_token_dict = y.get_access_token(code)
    access_token = access_token_dict["access_token"]

    # Getting YA user details
    yellowant_user = YellowAnt(access_token=access_token)
    profile = yellowant_user.get_user_profile()

    # Creating a new user integration for the application
    user_integration = yellowant_user.create_user_integration()
    hash_str = str(uuid.uuid4()).replace("-", "")[:25]
    ut = YellowUserToken.objects.create(user=user, yellowant_token=access_token,
                                        yellowant_id=profile['id'],
                                        yellowant_integration_invoke_name=user_integration \
                                            ["user_invoke_name"],
                                        yellowant_integration_id=user_integration \
                                            ['user_application'], webhook_id=hash_str)
    state = str(uuid.uuid4())
    AppRedirectState.objects.create(user_integration=ut, state=state)

    web_url = settings.BASE_URL + "/webhook/" + hash_str + "/"
    print(web_url)

    # Redirecting the user to the zoho oauth url to get the state and the auth code
    url = settings.ZOHO_OAUTH_URL
    params = {
        'scope': ','.join(str(i) for i in SCOPES),
        'client_id': settings.ZOHO_CLIENT_ID,
        'state': state,
        'response_type': 'code',
        'redirect_uri': settings.ZOHO_REDIRECT_URL,
        'access_type': 'offline',
        'prompt': 'Consent'
    }

    url += urllib.parse.urlencode(params)

    print(url)
    return HttpResponseRedirect(url)


def zohoRedirectUrl(request):
    """
     OAuth2 at zoho server
    """
    print("In ZohoRedirecturl")
    state = request.GET.get("state")
    print(state)

    zohoinvoice_redirect_state = AppRedirectState.objects.get(state=state)
    ut = zohoinvoice_redirect_state.user_integration
    error = request.GET.get('error', None)

    # Checking status of auth request
    if error == 'access_denied':
        return HttpResponse('Access denied')
    if state is None:
        return HttpResponseBadRequest()

    # Getting auth code
    auth_code = request.GET.get('code', None)

    if auth_code is None:
        return HttpResponseBadRequest()

    print("Auth_code")
    print(auth_code)

    url = settings.ZOHO_TOKEN_URL
    params = {
        'code': auth_code,
        'client_id': settings.ZOHO_CLIENT_ID,
        'client_secret': settings.ZOHO_CLIENT_SECRET,
        'redirect_uri': settings.ZOHO_REDIRECT_URL,
        'grant_type': 'authorization_code'
    }

    url += urllib.parse.urlencode(params)

    response = requests.post(url)
    print(response)
    print(response.text)
    response_json = response.json()
    access_token = response_json['access_token']
    refresh_token = response_json['refresh_token']

    # adding access and refresh token to the database

    ZohoInvoiceUserToken.objects.create(user_integration=ut,
                                        zoho_access_token=access_token,
                                        zoho_refresh_token=refresh_token)

    return HttpResponseRedirect("/")


@csrf_exempt
def add_new_contact(request, id):
    """
            Webhook function to notify user about newly added contact
    """
    # print("in contacts")
    # print(request.body)
    name = request.POST['name']
    contact_id = request.POST['ID']
    email = "-" if request.POST['email'] is None else request.POST['email']
    company_name = request.POST['company_name']

    # Fetching yellowant object
    yellow_obj = YellowUserToken.objects.get(webhook_id=id)
    access_token = yellow_obj.yellowant_token
    integration_id = yellow_obj.yellowant_integration_id
    # service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    webhook_message.message_text = "New contact added."
    attachment = MessageAttachmentsClass()

    field = AttachmentFieldsClass()
    field.title = "Contact Name"
    field.value = name
    attachment.attach_field(field)

    field1 = AttachmentFieldsClass()
    field1.title = "Contact ID"
    field1.value = contact_id
    attachment.attach_field(field1)

    field2 = AttachmentFieldsClass()
    field2.title = "Company Name"
    field2.value = company_name
    attachment.attach_field(field2)

    field3 = AttachmentFieldsClass()
    field3.title = "Email"
    field3.value = email
    attachment.attach_field(field3)

    webhook_message.attach(attachment)

    # print(integration_id)
    webhook_message.data = {
        "Name": name,
        "ID": contact_id,
        "Email": email,
        "Company Name": company_name
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="new_contact", **webhook_message.get_dict())
    return HttpResponse("OK", status=200)


@csrf_exempt
def add_new_item(request, id):
    """
            Webhook function to notify user about newly added item
    """
    # print("in contacts")
    print(request.body)
    name = request.POST['name']
    item_id = request.POST['ID']
    price = request.POST['price']
    description = request.POST['description']

    # Fetching yellowant object
    yellow_obj = YellowUserToken.objects.get(webhook_id=id)
    access_token = yellow_obj.yellowant_token
    integration_id = yellow_obj.yellowant_integration_id
    # service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    webhook_message.message_text = "New item added."

    attachment = MessageAttachmentsClass()

    field = AttachmentFieldsClass()
    field.title = "Item Name"
    field.value = name
    attachment.attach_field(field)

    field1 = AttachmentFieldsClass()
    field1.title = "Item ID"
    field1.value = item_id
    attachment.attach_field(field1)

    field2 = AttachmentFieldsClass()
    field2.title = "Price"
    field2.value = price
    attachment.attach_field(field2)

    field3 = AttachmentFieldsClass()
    field3.title = "Description"
    field3.value = description
    attachment.attach_field(field3)

    webhook_message.attach(attachment)
    # print(integration_id)
    webhook_message.data = {
        "Name": name,
        "ID": item_id,
        "Price": price,
        "Description": description,
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="new_item", **webhook_message.get_dict())
    return HttpResponse("OK", status=200)


@csrf_exempt
def add_new_invoice(request, id):
    """
            Webhook function to notify user about newly created invoice
    """
    print(request.body)
    invoice_id = request.POST['ID']
    contact_email = request.POST['Email']
    total = request.POST['Total']

    # Fetching yellowant object
    yellow_obj = YellowUserToken.objects.get(webhook_id=id)
    access_token = yellow_obj.yellowant_token
    integration_id = yellow_obj.yellowant_integration_id
    # service_application = str(integration_id)

    # Creating message object for webhook message
    webhook_message = MessageClass()
    webhook_message.message_text = "New invoice added"

    attachment = MessageAttachmentsClass()

    field = AttachmentFieldsClass()
    field.title = "Invoice ID"
    field.value = invoice_id
    attachment.attach_field(field)

    field1 = AttachmentFieldsClass()
    field1.title = "Total"
    field1.value = total
    attachment.attach_field(field1)

    field2 = AttachmentFieldsClass()
    field2.title = "Contact Email"
    field2.value = contact_email
    attachment.attach_field(field2)

    webhook_message.attach(attachment)
    # print(integration_id)
    webhook_message.data = {
        "Invoice ID": invoice_id,
        "Total": total,
        "Contact Email": contact_email,
    }

    # Creating yellowant object
    yellowant_user_integration_object = YellowAnt(access_token=access_token)

    # Sending webhook message to user
    yellowant_user_integration_object.create_webhook_message(
        requester_application=integration_id,
        webhook_name="new_invoice", **webhook_message.get_dict())
    return HttpResponse("OK", status=200)


@csrf_exempt
@require_POST
def webhook(request, id=None):
    """
        This function handles the incoming webhooks.
    """
    print(request.body)

    event_type = request.POST.get('type')
    print(event_type)

    if event_type == "contacts":
        # print("in pipeline webhook")
        add_new_contact(request, id)

    elif event_type == "item":
        # print("in user webhook")
        add_new_item(request, id)

    elif event_type == "invoice":
        # print("in deal webhook")
        add_new_invoice(request, id)

    return HttpResponse("OK", status=200)


@csrf_exempt
def yellowantapi(request):
    """
        Receive user commands from YA
    """
    try:

        # Extracting the necessary data
        data = json.loads(request.POST['data'])
        args = data["args"]
        service_application = data["application"]
        verification_token = data['verification_token']
        # function_id = data['function']
        function_name = data['function_name']
        # print(data)

        # Verifying whether the request is actually from YA using verification token
        if verification_token == settings.YELLOWANT_VERIFICATION_TOKEN:
            # Processing command in some class Command and sending a Message Object
            # Add_user and create_incident have flags to identify the status of the operation
            # and send webhook only if the operation is successful
            message = CommandCentre(data["user"], service_application, function_name, args).parse()

            # Returning message response
            return HttpResponse(message)
        else:
            # Handling incorrect verification token
            error_message = {"message_text": "Incorrect Verification token"}
            return HttpResponse(json.dumps(error_message), content_type="application/json")
    except Exception as e:
        # Handling exception
        print(str(e))
        traceback.print_exc()
        return HttpResponse("Something went wrong")
