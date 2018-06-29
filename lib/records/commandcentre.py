""""
    This is the command centre for all the commands created in the YA developer console
    This file contains the logic to understand a user message request from YA
    and return a response in the format of a YA message object accordingly

"""
import datetime
import json
import re
import urllib

import pytz
import requests
# from yellowant import YellowAnt
from yellowant.messageformat import MessageClass, MessageAttachmentsClass, AttachmentFieldsClass
from django.conf import settings
from .models import ZohoInvoiceUserToken, YellowUserToken


def get_token_from_refresh_token(refresh_token):
    # Build the post form for the token request
    # print("In get_token_from_refresh_token")

    url = settings.ZOHO_TOKEN_URL
    params = {
        'refresh_token': refresh_token,
        'client_id': settings.ZOHO_CLIENT_ID,
        'client_secret': settings.ZOHO_CLIENT_SECRET,
        'redirect_uri': settings.ZOHO_REDIRECT_URL,
        'grant_type': 'refresh_token'
    }
    # print("Getting new access token")
    url += urllib.parse.urlencode(params)
    response = requests.post(url)

    try:
        return response.json()
    except:
        return 'Error retrieving token: {0} - {1}'.format(response.status_code, response.text)

    test_ut = ZohoInvoiceUserToken.objects.get(user_integration=ut)
    test_ut.zoho_access_token = res_json['access_token']
    test_ut.save()


class CommandCentre(object):
    """ Handles user commands
        Args:
            yellowant_user_id(int) : The user_id of the user
            yellowant_integration_id (int): The integration id of a YA user
            function_name (str): Invoke name of the command the user is calling
            args (dict): Any arguments required for the command to run
     """

    def __init__(self, yellowant_user_id, yellowant_integration_id, function_name, args):
        self.yellowant_user_id = yellowant_user_id
        self.yellowant_integration_id = yellowant_integration_id
        self.function_name = function_name
        self.args = args
        self.user_integration = YellowUserToken.objects.get(yellowant_integration_id=self.yellowant_integration_id)
        self.zohoinvoice_object = ZohoInvoiceUserToken.objects.get(user_integration=self.user_integration)
        self.zohoinvoice_access_token = self.zohoinvoice_object.zoho_access_token
        self.zohoinvoice_refresh_token = self.zohoinvoice_object.zoho_refresh_token
        self.last_update = self.zohoinvoice_object.token_update

    def parse(self):
        """
            Matching which function to call
        """
        self.commands = {
            'list_users': self.list_users,
            'get_organization': self.get_organization,
            'create_contact': self.create_contact,
            'list_items': self.list_items,
            'create_item': self.create_item,
            'type_picklist': self.type_picklist,
            'add_user': self.add_user,
            'user_role_picklist': self.user_role_picklist,
            # 'create_contact_person': self.create_contact_person,
            'get_organization_customer_id': self.get_organization_customer_id,
            'create_invoice': self.create_invoice,
            'picklist_item': self.picklist_item,
        }

        # self.headers = {
        #     'Content-Type': 'application/json',
        #     }

        if self.last_update + datetime.timedelta(minutes=57) < pytz.utc.localize(datetime.datetime.utcnow()):
            token = get_token_from_refresh_token(self.zohoinvoice_refresh_token)
            print("Token is:")
            print(token)
            access_token = token['access_token']
            # refresh_token = token['refresh_token']
            ZohoInvoiceUserToken.objects.filter(user_integration=self.user_integration). \
                update(zoho_access_token=access_token,
                       token_update=datetime.datetime.utcnow())
            self.zohoinvoice_access_token = access_token

        return self.commands[self.function_name](self.args)

    def list_users(self, args):
        org_id = args['organization']
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Zoho-oauthtoken" + " " + self.zohoinvoice_access_token,
            "X-com-zoho-invoice-organizationid": org_id
        }
        url = settings.ZOHO_USER_URL
        response = requests.get(url, headers=headers)
        print(response)
        print(response.text)
        i = 0
        message = MessageClass()
        message.message_text = "Users"
        response_json = response.json()
        data = response_json['users']

        for user in data:
            attachment = MessageAttachmentsClass()
            attachment.image_url = user["photo_url"]
            attachment.text = "User" + " " + str(i+1)

            field1 = AttachmentFieldsClass()
            field1.title = "Name"
            field1.value = user['name']
            attachment.attach_field(field1)

            field2 = AttachmentFieldsClass()
            field2.title = "Email"
            field2.value = user['email']
            attachment.attach_field(field2)

            field3 = AttachmentFieldsClass()
            field3.title = "User ID"
            field3.value = user['user_id']
            attachment.attach_field(field3)

            field4 = AttachmentFieldsClass()
            field4.title = "Role ID"
            field4.value = user['role_id']
            attachment.attach_field(field4)
            i = i + 1
            message.attach(attachment)
        return message.to_json()

    def get_organization(self, args):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Zoho-oauthtoken" + " " + self.zohoinvoice_access_token
        }
        url = settings.ZOHO_ORGANIZATION_URL
        response = requests.get(url, headers=headers)
        # print(response.text)
        # print(type(response))
        response_json = response.json()
        # print(response_json)
        data = response_json['organizations']

        message = MessageClass()
        message.message_text = "Organization list:"

        name_list = {'org': []}
        for i in data:
            name_list['org'].append({"id": str(i['organization_id']), "name": str(i['name'])})
        message.data = name_list
        print(message.data)
        return message.to_json()

    def create_contact(self, args):
        org_id = args['organization']
        contact_name = args['contact_name']
        company_name = args['company_name']
        email = args['email']
        mobile = args['mobile']

        headers = {
            "Authorization": "Zoho-oauthtoken" + " " + self.zohoinvoice_access_token,
            "X-com-zoho-invoice-organizationid": org_id,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }
        url = settings.ZOHO_CONTACT_URL
        payload = {
            "contact_name": contact_name,
            "company_name": company_name,
            "contact_persons": [
                {
                    "email": email,
                    "mobile": mobile
                }
            ],
        }

        response = requests.post(url, headers=headers, data={"JSONString": json.dumps(payload)})
        response_json = response.json()
        print(response)
        print(response_json)

        message = MessageClass()
        if response.status_code == 400:
            attachment = MessageAttachmentsClass()

            field1 = AttachmentFieldsClass()
            field1.title = "Error"
            field1.value = response_json['message']
            attachment.attach_field(field1)

            message.attach(attachment)
            return message.to_json()
        else:
            contact_info = response_json["contact"]
            message.message_text = "The contact has been added"
            attachment = MessageAttachmentsClass()

            field1 = AttachmentFieldsClass()
            field1.title = "Contact Name"
            field1.value = contact_info['contact_name']
            attachment.attach_field(field1)

            field2 = AttachmentFieldsClass()
            field2.title = "Contact ID"
            field2.value = contact_info['contact_id']
            attachment.attach_field(field2)

            field3 = AttachmentFieldsClass()
            field3.title = "Company Name"
            field3.value = contact_info['company_name']
            attachment.attach_field(field3)

            message.attach(attachment)
            return message.to_json()

    def list_items(self, args):
        org_id = args['organization']
        headers = {
            "Authorization": "Zoho-oauthtoken" + " " + self.zohoinvoice_access_token,
            "X-com-zoho-invoice-organizationid": org_id,
            "Content-Type": "application/json"
        }
        url = settings.ZOHO_ITEMS_URL
        response = requests.get(url, headers=headers)
        print(response)
        print(response.text)
        message = MessageClass()
        message.message_text = "Items"
        response_json = response.json()
        data = response_json['items']
        i = 0
        print(data[0]['description'])
        a = data[0]['description']
        if len(a) == 0:
            print("its none")
        else:
            print("no")

        for item in data:
            attachment = MessageAttachmentsClass()
            attachment.text = "Item" + " " + str(i+1)

            field1 = AttachmentFieldsClass()
            field1.title = "Item Name"
            field1.value = item['name']
            attachment.attach_field(field1)

            field2 = AttachmentFieldsClass()
            field2.title = "Item ID"
            field2.value = item['item_id']
            attachment.attach_field(field2)

            field3 = AttachmentFieldsClass()
            field3.title = "Item Type"
            field3.value = item['product_type']
            attachment.attach_field(field3)

            field4 = AttachmentFieldsClass()
            field4.title = "Rate"
            field4.value = item['rate']
            attachment.attach_field(field4)

            des = item['description']
            field5 = AttachmentFieldsClass()
            field5.title = "Description"
            field5.value = "-" if len(des) == 0 else des
            attachment.attach_field(field5)
            i = i+1
            message.attach(attachment)
        return message.to_json()

    def type_picklist(self, args):
        """
                    This is a picklist function which gives two options.
                    Goods or Service
                """
        message = MessageClass()
        message.message_text = "Product Type"
        data = {'list': []}
        data['list'].append({"type": "goods"})
        data['list'].append({"type": "service"})
        # print(data)
        message.data = data
        return message.to_json()

    def create_item(self, args):
        org_id = args['organization']
        name = args['name']
        rate = args['Rate']
        product_type = args['product_type']
        print(product_type)
        description = args['description']

        headers = {
            "Authorization": "Zoho-oauthtoken" + " " + self.zohoinvoice_access_token,
            "X-com-zoho-invoice-organizationid": org_id,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }
        url = settings.ZOHO_ITEMS_URL
        payload = {
                    "name": name,
                    "rate": rate,
                    "description": description,
                    "product_type": product_type
                }

        response = requests.post(url, headers=headers, data={"JSONString": json.dumps(payload)})
        response_json = response.json()
        print(response)
        print(response_json)

        message = MessageClass()
        if response.status_code == 400:
            attachment = MessageAttachmentsClass()

            field1 = AttachmentFieldsClass()
            field1.title = "Error"
            field1.value = response_json['message']
            attachment.attach_field(field1)

            message.attach(attachment)
            return message.to_json()
        else:
            items_info = response_json["item"]
            message.message_text = "The item has been added"
            attachment = MessageAttachmentsClass()

            field1 = AttachmentFieldsClass()
            field1.title = "Item Name"
            field1.value = items_info['name']
            attachment.attach_field(field1)

            field2 = AttachmentFieldsClass()
            field2.title = "Item ID"
            field2.value = items_info['item_id']
            attachment.attach_field(field2)

            field3 = AttachmentFieldsClass()
            field3.title = "Item Description"
            field3.value = items_info['description']
            attachment.attach_field(field3)

            field4 = AttachmentFieldsClass()
            field4.title = "Item Type"
            field4.value = items_info['product_type']
            attachment.attach_field(field4)

            message.attach(attachment)
            return message.to_json()

    def add_user(self, args):
        org_id = args['organization']
        name = args['name']
        email = args['email']
        role = args['user_role']

        headers = {
            "Authorization": "Zoho-oauthtoken" + " " + self.zohoinvoice_access_token,
            "X-com-zoho-invoice-organizationid": org_id,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }
        url = settings.ZOHO_USER_URL
        payload = {
                    "name": name,
                    "email": email,
                    "user_role": role
                }

        response = requests.post(url, headers=headers, data={"JSONString": json.dumps(payload)})
        response_json = response.json()
        print(response)
        print(response_json)

        message = MessageClass()

        if response.status_code == 400:
            attachment = MessageAttachmentsClass()

            field1 = AttachmentFieldsClass()
            field1.title = "Error"
            field1.value = response_json['message']
            attachment.attach_field(field1)

            message.attach(attachment)
            return message.to_json()
        else:
            attachment = MessageAttachmentsClass()
            attachment.text = "Your invitation has been sent."
            message.attach(attachment)
            return message.to_json()

    def user_role_picklist(self, args):
        message = MessageClass()
        message.message_text = "User Role"
        data = {'list': []}
        data['list'].append({"role": "admin"})
        data['list'].append({"role": "staff"})
        data['list'].append({"role": "timesheetstaff"})
        # data['list'].append({"role": "goods"})

        message.data = data
        return message.to_json()

    # def create_contact_person(self, args):
    #     org_id = args['organization']
    #     first_name = args['first_name']
    #     # last_name = args['last_name']
    #     email = args['email']
    #     mobile = args['mobile']
    #
    #     headers = {
    #         "Authorization": "Zoho-oauthtoken" + " " + self.zohoinvoice_access_token,
    #         "X-com-zoho-invoice-organizationid": org_id,
    #         "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    #     }
    #     url = settings.ZOHO_CONTACT_PERSON_URL
    #     payload = {
    #                 "first_name": first_name,
    #                 # "last_name": last_name,
    #                 "email": email,
    #                 "mobile": mobile
    #             }
    #
    #     response = requests.post(url, headers=headers, data={"JSONString": json.dumps(payload)})
    #     response_json = response.json()
    #     print(response)
    #     print(response_json)
    #
    #     message = MessageClass()
    #     if response.status_code == 400:
    #         attachment = MessageAttachmentsClass()
    #
    #         field1 = AttachmentFieldsClass()
    #         field1.title = "Error"
    #         field1.value = "Invalid value passed for email"
    #         attachment.attach_field(field1)
    #
    #         message.attach(attachment)
    #         return message.to_json()
    #     else:
    #         # contact_info = response_json["contact"]
    #         message.message_text = "The contact person has been added"
    #         attachment = MessageAttachmentsClass()
    #
    #         # field1 = AttachmentFieldsClass()
    #         # field1.title = "Contact Name"
    #         # field1.value = contact_info['contact_name']
    #         # attachment.attach_field(field1)
    #         #
    #         # field2 = AttachmentFieldsClass()
    #         # field2.title = "Contact ID"
    #         # field2.value = contact_info['contact_id']
    #         # attachment.attach_field(field2)
    #         #
    #         # field3 = AttachmentFieldsClass()
    #         # field3.title = "Company Name"
    #         # field3.value = contact_info['company_name']
    #         # attachment.attach_field(field3)
    #
    #         message.attach(attachment)
    #         return message.to_json()

    def get_organization_customer_id(self, args):
        org_headers = {
            "Content-Type": "application/json",
            "Authorization": "Zoho-oauthtoken" + " " + self.zohoinvoice_access_token
        }
        url = settings.ZOHO_ORGANIZATION_URL
        response = requests.get(url, headers=org_headers)
        # print(response.text)
        # print(type(response))
        response_json = response.json()
        print(response_json)
        data = response_json['organizations']

        for i in data:
            org_id = i['organization_id']
            headers = {
                "Authorization": "Zoho-oauthtoken" + " " + self.zohoinvoice_access_token,
                "X-com-zoho-invoice-organizationid": org_id,
                "Content-Type": "application/json"
            }
            url = settings.ZOHO_CONTACT_URL
            response = requests.get(url, headers=headers)
            print(response)
            print(response.text)
            response_json = response.json()
            message = MessageClass()
            message.message_text = "Customer list:"
            data = response_json['contacts']
            name_list = {'data': []}
            for a in data:
                name_list['data'].append({"id": str(a['contact_id']), "name": str(a['contact_name'])})
            message.data = name_list
            print(message.data)
            return message.to_json()

    def picklist_item(self,args):
        org_headers = {
            "Content-Type": "application/json",
            "Authorization": "Zoho-oauthtoken" + " " + self.zohoinvoice_access_token
        }
        url = settings.ZOHO_ORGANIZATION_URL
        response = requests.get(url, headers=org_headers)
        # print(response.text)
        # print(type(response))
        response_json = response.json()
        print(response_json)
        data = response_json['organizations']

        for i in data:
            org_id = i['organization_id']
            headers = {
                "Authorization": "Zoho-oauthtoken" + " " + self.zohoinvoice_access_token,
                "X-com-zoho-invoice-organizationid": org_id,
                "Content-Type": "application/json"
            }
            url = settings.ZOHO_ITEMS_URL
            response = requests.get(url, headers=headers)
            print(response)
            print(response.text)
            response_json = response.json()
            message = MessageClass()
            message.message_text = "Item list:"
            data = response_json['items']
            name_list = {'data': []}
            for a in data:
                name_list['data'].append({"id": str(a['item_id']), "name": str(a['name'])})
            message.data = name_list
            print(message.data)
            return message.to_json()

    def create_invoice(self, args):
        org_id = args['organization']
        customer_id = args['customer_id']
        date = args['date']
        item_id = args['item_id']
        quantity = args['quantity']

        # org_id = "669665442"
        # customer_id = "1392605000000069001"
        # date = "2018-07-27"
        # item_id = "1392605000000072001"
        # quantity = 1

        headers = {
            "Authorization": "Zoho-oauthtoken" + " " + self.zohoinvoice_access_token,
            "X-com-zoho-invoice-organizationid": org_id,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
        }
        url = settings.ZOHO_INVOICE_URL
        payload = {
                    "customer_id": customer_id,
                    "date": date,
                    "line_items": [
                        {
                            "item_id": item_id,
                            "quantity": quantity,
                        }
                    ],
        }

        response = requests.post(url, headers=headers, data={"JSONString": json.dumps(payload)})
        response_json = response.json()
        print(response)
        print(response_json)

        message = MessageClass()

        if response.status_code == 400:
            attachment = MessageAttachmentsClass()

            field1 = AttachmentFieldsClass()
            field1.title = "Error"
            field1.value = response_json['message']
            attachment.attach_field(field1)

            message.attach(attachment)
            return message.to_json()
        else:
            attachment = MessageAttachmentsClass()
            attachment.text = "Invoice created"
            message.attach(attachment)
            return message.to_json()








