export class AccountSettingsController {
  
  userAccount;

  constructor(AppApi, $stateParams, $mdDialog, $mdToast, $state) {
    this.AppApi = AppApi;
    this.$stateParams = $stateParams;
    this.$mdDialog = $mdDialog;
    this.$mdToast = $mdToast;
    this.$state = $state;
    this.userAccount = {};
  }

  $onInit() {
    if (this.$stateParams.accountId) {
      this.AppApi.getUserAccount(this.$stateParams.accountId)
        .then((successResponse) => {
          this.userAccount = successResponse.data;
        }, (errorResponse) => {
          this.userAccount = null;
        });
    } else {
      this.userAccount = null;
    }
  }

  goBack = function(){
        this.$state.go('accountList')
  }

  submitForm = function(){
        this.AppApi.submitForm({
                 'pipedrive_api_token': this.accountDetails.api_token,
                 'user_integration': this.$stateParams.accountId,
				      })
					  .then(function(response){
					    console.log("success")
					  	this.$mdToast.show(this.$mdToast.simple().textContent(response.data));
					    }.bind(this) ,
					    function(response){
					        console.log("fail")
					        this.$mdToast.show(this.$mdToast.simple().textContent("Invalid credentials"));
					    }.bind(this));
  }

  /*submitSettings = function(){
	    this.AppApi.submitSettings({
	                            'new_api_key': this.accountDetails.api_key,
	                            'integration_id': this.integration_id,}).then(function(response){
									if(response.status==200){
									    this.$mdToast.show(this.$mdToast.simple().textContent(response.data);
									    }
	                                else{
	                                    this.$mdToast.show(this.$mdToast.simple().textContent("Something went wrong, try again later");
	                                    }
	                                 });
	}*/

  deleteAccount() {
  console.log("deleting");
    this.AppApi.deleteUserAccount(this.$stateParams.accountId)
      .then((successResponse) => {
        this.$state.go("accountList");
        this.$mdToast.show(this.$mdToast.simple().textContent('Your integration has been successfully removed'));
      }, (errorResponse) => {
        this.$mdToast.show(this.$mdToast.simple().textContent('Unable to remove your account at the moment'));
      });
  }

  onDeleteAccount() {
    var confirm = this.$mdDialog.confirm()
          .title("Would you like to remove this Pipedrive integration with Yellowant?")
          .ariaLabel("pipedrive Handle")
          .clickOutsideToClose(true)
          .ok('Delete Integration')
          .cancel('Cancel');

    this.$mdDialog.show(confirm).then(() =>
    {
      this.deleteAccount()
    }, function() { });
  }


  onDeleteWebhook(webhook) {
    var confirm = this.$mdDialog.confirm()
          .title(`Would you like to remove your webhook ${webhook.id} for "${webhook.repo_full_name}"?`)
          .clickOutsideToClose(true)
          .ok('Delete Webhook')
          .cancel('Cancel');

    this.$mdDialog.show(confirm).then(() =>
    {
      this.deleteWebhook(webhook);
    }, function() { });
  }

  deleteWebhook(webhook) {
    this.AppApi.deleteUserWebhook(this.$stateParams.accountId, webhook.id)
      .then((successResponse) => {
        this.$mdToast.show(this.$mdToast.simple().textContent('Deleted webhook successfully!'));
        webhook.is_deleted = true;
      }, (errorResponse) => {
        this.$mdToast.show(this.$mdToast.simple().textContent('Unable to delete the webhook at the moment'));
      });
  }


}

