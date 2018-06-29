export class AccountListController {
  
  userAccounts;
  userStates;

  constructor(AppApi, $stateParams, $mdDialog, $mdToast, $state) {
    this.AppApi = AppApi;
    this.$stateParams = $stateParams;
    this.$mdDialog = $mdDialog;
    this.$mdToast = $mdToast;
    this.$state = $state;
  }


  $onInit() {
    this.AppApi.getUserAccounts()
      .then((successResponse) => {
        this.userAccounts = successResponse.data;
      }, (errorResponse) => {
        this.userAccounts = null;
      });
  }

  stateDetails(id){
    this.AppApi.getStateDetails(id)
      .then((successResponse) => {
        this.userStates = successResponse.data;
      },(errorResponse)=>{
        this.userStates =null;
      });
  }

  deleteAccount(id) {
    this.AppApi.deleteUserAccount(id)
      .then((successResponse) => {
        this.userAccounts = this.userAccounts.filter(userAccount=>userAccount.id !== id);
        this.$mdToast.show(this.$mdToast.simple().textContent('Your integration has been successfully removed'));
      }, (errorResponse) => {
          console.log("Error is:")
          console.log(errorResponse)
        this.$mdToast.show(this.$mdToast.simple().textContent('Unable to remove your account at the moment'));
      });
  }
  onDeleteAccount(userAccount) {
    console.log(userAccount)
    var confirm = this.$mdDialog.prompt()
          .title("Would you like to remove this Zoho Invoice integration with Yellowant?")
          .textContent(`Please type in your victorops handle to confirm: ${userAccount.user_invoke_name}`)
          .placeholder("zohoinvoice-handle")
          .ariaLabel("zohoinvoice Handle")
          .clickOutsideToClose(true)
          .ok('Delete Integration')
          .cancel('Cancel');

    this.$mdDialog.show(confirm).then((result) =>
    {
      if (result == userAccount.user_invoke_name) {
        this.deleteAccount(userAccount.id);
      }
      else
        this.onDeleteAccount(userAccount);
    }, function() { });
  }

}