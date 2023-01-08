$(document).ready(function() {
    var elementExists = document.getElementById("ps_list");
    if (elementExists) {
    	console.log("hello")
        const availablePSsArray = JSON.parse(document.getElementById('ps_list').textContent);

         availablePSs = availablePSsArray.map(x => " ".concat(x[1]));
        console.log(availablePSs)
    };

    $(document).on('focus', "input[id$='date']", function() {
    selected_id = "#" + $(this).first().attr("id");

    $(selected_id).datepicker({
        dateFormat: 'yy-mm-dd'
    });
    $(selected_id).change(function() {
        $(selected_id).datepicker("destroy");
    });

});

$(document).on('focus', "input[id$='police_station_with_distt']", function() {
    selected_id = "#" + $(this).first().attr("id");
    $(selected_id).autocomplete({
        source: availablePSs,
        change: function(event, ui) {
            // This block of code ensures that values are restricted to list items
            if (ui.item == null) {
                event.currentTarget.value = '';
                event.currentTarget.focus();
            }
            // This block of code ensures that values are restricted to list items
            else {
                $(selected_id).autocomplete("destroy");
            }
        }

    });


});

});
