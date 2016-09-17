$(document).ready(function(){
    updater.poll();
})

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


var updater = {
    errorSleepTime: 500,

    poll: function() {
        var args = {"_xsrf": getCookie("_xsrf")};
        $.ajax({url: "/listen", type: "POST", dataType: "text",
                data: $.param(args), success: updater.onSuccess,
                error: updater.onError});
    },

    onSuccess: function(response) {
        try {
            updater.newMessages(eval("(" + response + ")"));
        } catch (e) {
            updater.onError();
            return;
        }
        updater.errorSleepTime = 500;
        window.setTimeout(updater.poll, 0);
    },

    onError: function(response) {
        updater.errorSleepTime *= 2;
        console.log("Poll error; sleeping for", updater.errorSleepTime, "ms");
        window.setTimeout(updater.poll, updater.errorSleepTime);
    },

    newMessages: function(response) {
        if (!response.message) return;
        var message = response.message;
        updater.showMessage(message);
    },

    showMessage: function(message) {
        var node = $("<div class='message'>"+message+"</div>");
        node.hide();
        $(".messages_container").append(node);
        node.slideDown();
    }
};