//********************************* STARTs HERE ***********
//For User input form validation error message
var message;
function commonPnotify(type,message) {
    var opts = {
        shadow: false
    };
    switch (type) {
        case 'userInputValidationError':
            opts.title ="Error :)";
            opts.text = "Please enter URL and Goal properly then try to submit.";
            opts.type = "info";
            break;
        case 'newSearchValue':
            opts.title ="Success :)";
            opts.text = "New ULR has set successfully.Click on submit button to search again.";
            opts.type = "info";
            break;
        
     }
     new PNotify(opts);
  }

//SET new link
$('.set_search_with').click(function() {
      var new_search_val = $(this).attr('set_search_value');
      commonPnotify('newSearchValue');
      $("#input_url").val(new_search_val);
    });



var form = $("#aueForm");
form.validate({
       rules: {
            input_url: {
              required:true,
              // url:true,
            },
            input_goal: "required",
      },
        messages: {
            input_url:{
            required:"URL cannot be blank",
            // url : "Enter a valid url. Example http://www.amazon.in ",
          },
            input_goal: "Goal cannot be blank",
          }
});



$(document).ready(function(){

  
    $('[data-toggle="tooltip"]').tooltip();
$("#user_input_submit").removeAttr('disabled','disabled');
    $("#user_input_submit").click(function(){
      
      function GetQueryStringParams(sParam){
    var sPageURL = window.location.search.substring(1);
    var sURLVariables = sPageURL.split('&');
    for (var i = 0; i < sURLVariables.length; i++) 
    {
        var sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] == sParam) 
        {
            return sParameterName[1];
        }
    }
}
      $(".record_tr").hide();
      var input_url = $("#input_url").val();
      var input_goal = $("#input_goal").val();
      var type = GetQueryStringParams('type')
      var min_score = GetQueryStringParams('min_score')
      // console.log("type"+type+"min_score"+min_score);
      $("#user_input_submit").attr('disabled','disabled');
      $("#aue_not_found").hide();
      $("#aueTable").hide();
      formValidation=form.valid();
    
    if(formValidation == false){
        commonPnotify('userInputValidationError');
        $("#user_input_submit").removeAttr('disabled','disabled');
        }
       else{
  
  $("#aueLoadingSpinner").show();
  $(".loading_div").show();
  
    $.ajax({
    url : "get-search-result/", 
    type : "POST", 
    timeout: '6000000000',
    data : { input_url : input_url,input_goal : input_goal,type : type,min_score:min_score }, 
    success : function(data) {
      $(".loading_div").hide();
      $("#aueLoadingSpinner").hide();
      var search_result = data["search_result"]
      counter  = 1
      for (i = 0; i < search_result.length; i++) {
        $("#aueTable").show();
        $("#aue_not_found").hide();
        $("#record_tr_"+counter).show();
          result_url = search_result[i]

          $("#s_no_"+counter).text(counter);
          $("#url_no_"+counter).text(result_url);
          $("#action_no_"+counter).attr("href",result_url);
          $("#set_search_with_"+counter).attr("set_search_value",result_url);
          counter ++;
        }
        if(search_result.length <= 0){
          $("#aue_not_found").show();
          $("#aueTable").hide();
        }
        $("#user_input_submit").removeAttr('disabled','disabled');
        },
    error : function(xhr,errmsg,err) {
      alert("Timeout error.Please check your internet connection or enter a valid url and then try again "+errmsg);
         console.log(xhr.status + ": " + xhr.responseText+"xhr"+xhr+"err"+err);
         $("#user_input_submit").removeAttr('disabled','disabled');
         $("#aueLoadingSpinner").hide();
         $(".loading_div").hide();
    }
});
}

});
});



