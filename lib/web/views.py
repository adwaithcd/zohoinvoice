"""
Functions corresponding to URL patterns of web app

"""
import json
import requests
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from yellowant import YellowAnt
from ..records.models import YellowUserToken, ZohoInvoiceUserToken


def index(request, path):
    """
        Loads the homepage of the app.
        index function loads the home.html page
    """
    # print('test')

    context = {
        "base_href": settings.BASE_HREF,
        "application_id": settings.YELLOWANT_APP_ID,
        "user_integrations": []
    }
    # Check if user is authenticated otherwise redirect user to login page
    if request.user.is_authenticated:
        user_integrations = YellowUserToken.objects.filter(user=request.user.id)
        # print(user_integrations)
        # for user_integration in user_integrations:
        #     context["user_integrations"].append(user_integration)
    return render(request, "home.html", context)


def userdetails(request):
    """
        userdetails function shows the vital integration details of the user
    """
    # print("in userdetails")
    user_integrations_list = []
    # Returns the integration id,user_invoke_name for an integration
    if request.user.is_authenticated:
        user_integrations = YellowUserToken.objects.filter(user=request.user.id)
        print(user_integrations)
        for user_integration in user_integrations:
            try:
                pdut = ZohoInvoiceUserToken.objects.get(user_integration=user_integration)
                print(pdut)
                user_integrations_list.append({"user_invoke_name": user_integration.\
                                              yellowant_integration_invoke_name,
                                               "id": user_integration.id, "app_authenticated": True,
                                               })
            except ZohoInvoiceUserToken.DoesNotExist:
                user_integrations_list.append({"user_invoke_name": user_integration.\
                                              yellowant_integration_invoke_name,
                                               "id": user_integration.id,
                                               "app_authenticated": False})
    return HttpResponse(json.dumps(user_integrations_list), content_type="application/json")


def user_detail_update_delete_view(request, id=None):
    """
        This function handles the updating, deleting and viewing user details
    """
    print("In user_detail_update_delete_view")
    print(id)
    user_integration_id = id
    # if request.method == "GET":
    #     # return user data
    #     print("in get")
    #     pdut = ZohoInvoiceUserToken.objects.get(user_integration=user_integration_id)
    #     return HttpResponse(json.dumps({
    #         "is_valid": pdut.apikey_login_update_flag
    #     }))

    if request.method == "DELETE":
        # deletes the integration
        print("In delete_integration")
        # print(id)this is a test subject
        # print("user is ", request.user.id)
        access_token_dict = YellowUserToken.objects.get(id=id)
        user_id = access_token_dict.user
        # print("id is ", user_id)
        if user_id == request.user.id:
            access_token = access_token_dict.yellowant_token
            user_integration_id = access_token_dict.yellowant_integration_id
            print(user_integration_id)
            url = "https://api.yellowant.com/api/user/integration/%s" % (user_integration_id)
            yellowant_user = YellowAnt(access_token=access_token)
            yellowant_user.delete_user_integration(id=user_integration_id)
            response_json = YellowUserToken.objects.get(yellowant_token=access_token).delete()
            print(response_json)
            return HttpResponse("successResponse", status=204)
        else:
            return HttpResponse("Not Authenticated", status=403)

